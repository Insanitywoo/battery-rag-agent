from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import get_session_factory
from app.models.experiment_dataset import ExperimentDataset
from app.models.experiment_output import ExperimentOutput

from test_agent_framework import create_project, login_user, register_user


def upload_dataset(
    client: TestClient,
    *,
    project_id: str,
    filename: str,
    content: bytes,
    content_type: str = "text/csv",
):
    return client.post(
        f"/api/projects/{project_id}/experiments/datasets",
        files={"upload": (filename, content, content_type)},
    )


def test_owner_can_upload_preview_analyze_and_export_experiment_dataset(client: TestClient) -> None:
    register_user(client, name="Alice", email="alice@example.com", password="secret123")
    login_user(client, email="alice@example.com", password="secret123")
    project_id = create_project(client, name="Experiment Workspace")

    dataset_response = upload_dataset(
        client,
        project_id=project_id,
        filename="cycling-results.csv",
        content=(
            b"cycle,capacity,temperature\n"
            b"1,98.5,25\n"
            b"2,97.3,28\n"
            b"3,96.1,31\n"
            b"4,95.2,35\n"
        ),
    )
    assert dataset_response.status_code == 201
    dataset_payload = dataset_response.json()
    assert dataset_payload["row_count"] == 4
    assert any(column["name"] == "capacity" for column in dataset_payload["columns"])

    detail_response = client.get(f"/api/projects/{project_id}/experiments/datasets/{dataset_payload['id']}")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert len(detail_payload["preview_rows"]) == 4
    assert detail_payload["preview_rows"][0]["cycle"] == "1"

    stats_response = client.post(f"/api/projects/{project_id}/experiments/datasets/{dataset_payload['id']}/stats", json={})
    assert stats_response.status_code == 201
    stats_payload = stats_response.json()
    assert stats_payload["output_type"] == "stats_summary"
    assert "capacity" in stats_payload["stats_json"]

    chart_response = client.post(
        f"/api/projects/{project_id}/experiments/datasets/{dataset_payload['id']}/charts",
        json={
            "chart_type": "line",
            "x_field": "cycle",
            "y_field": "capacity",
            "title": "Capacity by Cycle",
        },
    )
    assert chart_response.status_code == 201
    chart_payload = chart_response.json()
    assert chart_payload["output_type"] == "line_chart"
    assert chart_payload["chart_path"]

    chart_file_response = client.get(f"/api/projects/{project_id}/experiments/outputs/{chart_payload['id']}/chart")
    assert chart_file_response.status_code == 200
    assert chart_file_response.headers["content-type"].startswith("image/svg+xml")
    assert "<svg" in chart_file_response.text

    analysis_response = client.post(
        f"/api/projects/{project_id}/experiments/datasets/{dataset_payload['id']}/analysis",
        json={
            "title": "Capacity retention note",
            "prompt": "Focus on how capacity changes across the recorded cycles.",
        },
    )
    assert analysis_response.status_code == 201
    analysis_payload = analysis_response.json()
    assert analysis_payload["output_type"] == "result_analysis"
    assert "Need manual confirmation" in analysis_payload["content_markdown"]

    outputs_response = client.get(f"/api/projects/{project_id}/experiments/outputs")
    assert outputs_response.status_code == 200
    assert len(outputs_response.json()) == 3

    markdown_export = client.get(f"/api/projects/{project_id}/experiments/outputs/{stats_payload['id']}/export/markdown")
    assert markdown_export.status_code == 200
    assert markdown_export.headers["content-type"].startswith("text/markdown")
    assert "Statistics Summary" in markdown_export.text

    latex_export = client.get(f"/api/projects/{project_id}/experiments/outputs/{stats_payload['id']}/export/latex")
    assert latex_export.status_code == 200
    assert latex_export.headers["content-type"].startswith("application/x-tex")
    assert "\\begin{table}" in latex_export.text

    with get_session_factory()() as session:
        dataset = session.scalar(select(ExperimentDataset).where(ExperimentDataset.id == dataset_payload["id"]))
        assert dataset is not None
        assert dataset.user_id == dataset_payload["user_id"]
        assert dataset.project_id == project_id
        output = session.scalar(select(ExperimentOutput).where(ExperimentOutput.id == analysis_payload["id"]))
        assert output is not None
        assert output.user_id == dataset_payload["user_id"]
        assert output.project_id == project_id
        assert output.dataset_id == dataset_payload["id"]


def test_experiment_routes_reject_invalid_uploads_and_remain_owner_scoped(app) -> None:
    with TestClient(app) as alice_client, TestClient(app) as bob_client, TestClient(app) as anon_client:
        register_user(alice_client, name="Alice", email="alice@example.com", password="secret123")
        login_user(alice_client, email="alice@example.com", password="secret123")
        project_id = create_project(alice_client, name="Owner Experiment Project")

        invalid_type_response = upload_dataset(
            alice_client,
            project_id=project_id,
            filename="notes.txt",
            content=b"not,csv",
            content_type="text/plain",
        )
        assert invalid_type_response.status_code == 400

        oversize_response = upload_dataset(
            alice_client,
            project_id=project_id,
            filename="too-large.csv",
            content=b"cycle,capacity\n" + (b"1,98.0\n" * 400),
        )
        assert oversize_response.status_code == 413

        valid_response = upload_dataset(
            alice_client,
            project_id=project_id,
            filename="owner-data.csv",
            content=b"label,phase\nA,baseline\nB,repeat\n",
        )
        assert valid_response.status_code == 201
        dataset_id = valid_response.json()["id"]

        register_user(bob_client, name="Bob", email="bob@example.com", password="secret123")
        login_user(bob_client, email="bob@example.com", password="secret123")

        assert anon_client.get(f"/api/projects/{project_id}/experiments/datasets").status_code == 401
        assert bob_client.get(f"/api/projects/{project_id}/experiments/datasets").status_code == 404
        assert bob_client.get(f"/api/projects/{project_id}/experiments/datasets/{dataset_id}").status_code == 404
        assert bob_client.delete(f"/api/projects/{project_id}/experiments/datasets/{dataset_id}").status_code == 404

        no_numeric_response = alice_client.post(f"/api/projects/{project_id}/experiments/datasets/{dataset_id}/stats", json={})
        assert no_numeric_response.status_code == 400
