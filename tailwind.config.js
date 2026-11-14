/** Design tokens taken from the reference: warm cream, ink, coral, teal, mustard. */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        cream: "#F4EFE6",
        paper: "#FBF8F2",
        ink: "#14120F",
        coral: "#F26440",
        teal: "#2D6A8A",
        mustard: "#EBA52B",
        line: "#E0D9CB",
      },
      fontFamily: {
        display: ['"Bricolage Grotesque"', "system-ui", "sans-serif"],
        sans: ['"Inter Tight"', "system-ui", "sans-serif"],
      },
      borderRadius: { xl2: "1.5rem" },
    },
  },
  plugins: [],
};
