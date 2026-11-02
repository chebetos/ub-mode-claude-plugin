export default {
  extends: ["@commitlint/config-conventional"],
  ignores: [(message) => message.startsWith("chore(release):")],
  rules: {
    "subject-exclamation-mark": [2, "never"],
    "scope-enum": [
      2,
      "always",
      [
        "upstream/ub-mode",
        "upstream/crapper",
        "upstream/dryer",
        "upstream/mutator",
        "upstream/uml-viewer",
        "scripts",
        "plugin",
        "ci",
        "sync",
        "docs",
      ],
    ],
  },
};
