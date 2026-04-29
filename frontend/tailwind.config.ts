import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#0b1324",
        mist: "#f5f7fb",
        cobalt: "#1d4ed8",
        ember: "#ea580c",
      },
    },
  },
  plugins: [],
};

export default config;
