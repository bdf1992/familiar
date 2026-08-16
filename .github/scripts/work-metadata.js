const PRIORITY = {
  P0: { color: "B60205", description: "Correctness boundary: current invariant or fail-closed defect" },
  P1: { color: "D93F0B", description: "Required integration or integrity work" },
  P2: { color: "FBCA04", description: "Portability, governance, or maintainability work" },
  P3: { color: "0E8A16", description: "Exploratory or optional active work" },
};

const TYPES = new Set(["bug", "enhancement", "documentation"]);

function escapeRegex(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function field(body, name) {
  const pattern = new RegExp(`^-\\s*\\*\\*${escapeRegex(name)}:\\*\\*\\s*(.+)$`, "mi");
  const match = (body || "").match(pattern);
  return match ? match[1].trim() : "";
}

function hasHeading(body, heading) {
  return (body || "").split(/\r?\n/).some((line) => new RegExp(`^##\\s+${escapeRegex(heading)}\\s*$`, "i").test(line));
}

function section(body, heading) {
  const lines = (body || "").split(/\r?\n/);
  const headingPattern = new RegExp(`^##\\s+${escapeRegex(heading)}\\s*$`, "i");
  const start = lines.findIndex((line) => headingPattern.test(line));
  if (start < 0) return "";
  const next = lines.findIndex((line, index) => index > start && /^##\s+/.test(line));
  return lines.slice(start + 1, next < 0 ? lines.length : next).join("\n").trim();
}

function parseIssue(body) {
  const typeRaw = field(body, "Type");
  const priorityRaw = field(body, "Priority");
  const domain = field(body, "Domain");
  const depends = field(body, "Depends on");
  const blocks = field(body, "Blocks");
  const related = field(body, "Related");

  const typeMatch = typeRaw.toLowerCase().match(/\b(bug|enhancement|documentation)\b/);
  const priorityMatch = priorityRaw.toUpperCase().match(/\b(P[0-3])\b/);
  const type = typeMatch ? typeMatch[1] : "";
  const priority = priorityMatch ? priorityMatch[1] : "";

  const errors = [];
  if (!typeRaw || typeRaw.includes("|") || !TYPES.has(type)) errors.push("Type must be exactly bug, enhancement, or documentation.");
  if (!priorityRaw || priorityRaw.includes("|") || !PRIORITY[priority]) errors.push("Priority must resolve to exactly P0, P1, P2, or P3.");
  if (!domain || domain.includes("|")) errors.push("Domain must name the owning domain or Cross-domain.");
  if (!depends) errors.push("Depends on must be present; use none when empty.");
  if (!blocks) errors.push("Blocks must be present; use none when empty.");
  if (!related) errors.push("Related must be present; use none when empty.");
  for (const heading of ["Problem", "Specification", "Acceptance criteria"]) {
    if (!hasHeading(body, heading)) errors.push(`Missing ## ${heading} section.`);
  }

  return { type, priority, errors };
}

async function ensureLabel(github, owner, repo, name, color, description) {
  try {
    await github.rest.issues.getLabel({ owner, repo, name });
  } catch (error) {
    if (error.status !== 404) throw error;
    await github.rest.issues.createLabel({ owner, repo, name, color, description });
  }
}

async function removeLabelIfPresent(github, owner, repo, issueNumber, labels, name) {
  if (!labels.has(name)) return;
  try {
    await github.rest.issues.removeLabel({ owner, repo, issue_number: issueNumber, name });
  } catch (error) {
    if (error.status !== 404) throw error;
  }
  labels.delete(name);
}

async function validateIssue({ github, owner, repo, issue, commentOnInvalid }) {
  const parsed = parseIssue(issue.body || "");
  const labels = new Set((issue.labels || []).map((label) => typeof label === "string" ? label : label.name));
  const wasInvalid = labels.has("invalid");

  if (parsed.errors.length) {
    if (!wasInvalid) {
      await github.rest.issues.addLabels({ owner, repo, issue_number: issue.number, labels: ["invalid"] });
      labels.add("invalid");
      if (commentOnInvalid) {
        await github.rest.issues.createComment({
          owner,
          repo,
          issue_number: issue.number,
          body: `<!-- work-metadata-validator -->\nThis issue is missing required repository work metadata:\n\n${parsed.errors.map((error) => `- ${error}`).join("\n")}\n\nRepair the metadata block using \`.github/ISSUE_TEMPLATE/work-item.md\`. The \`invalid\` label is removed automatically once the issue conforms.`,
        });
      }
    }
    return { valid: false, errors: parsed.errors };
  }

  await removeLabelIfPresent(github, owner, repo, issue.number, labels, "invalid");

  for (const candidate of TYPES) {
    if (candidate !== parsed.type) await removeLabelIfPresent(github, owner, repo, issue.number, labels, candidate);
  }
  if (!labels.has(parsed.type)) {
    await github.rest.issues.addLabels({ owner, repo, issue_number: issue.number, labels: [parsed.type] });
    labels.add(parsed.type);
  }

  const priorityLabel = `priority:${parsed.priority}`;
  const prioritySpec = PRIORITY[parsed.priority];
  await ensureLabel(github, owner, repo, priorityLabel, prioritySpec.color, prioritySpec.description);
  for (const candidate of Object.keys(PRIORITY)) {
    const label = `priority:${candidate}`;
    if (label !== priorityLabel) await removeLabelIfPresent(github, owner, repo, issue.number, labels, label);
  }
  if (!labels.has(priorityLabel)) {
    await github.rest.issues.addLabels({ owner, repo, issue_number: issue.number, labels: [priorityLabel] });
  }

  return { valid: true, errors: [] };
}

function validatePullRequest(body) {
  const errors = [];
  for (const heading of ["Work", "Change", "Metadata impact", "Validation", "Residuals"]) {
    if (!hasHeading(body, heading)) errors.push(`Missing ## ${heading} section.`);
  }

  const issue = field(body, "Issue");
  const domains = field(body, "Domains");
  const lifecycle = field(body, "Lifecycle crossing");
  const audit = field(body, "Audit impact");
  const residuals = section(body, "Residuals");

  if (!issue || issue.includes("|") || (!/#\d+/.test(issue) && !/^none\b/i.test(issue))) {
    errors.push("Issue must reference #N or state none with a reason.");
  }
  if (!domains || domains.includes("|")) errors.push("Domains must be explicitly resolved.");
  if (!lifecycle || lifecycle.includes("|")) errors.push("Lifecycle crossing must be explicit, including none.");
  if (!audit || audit.includes("|")) errors.push("Audit impact must be explicit, including none.");
  if (!residuals || residuals.includes("|")) errors.push("Residuals must be explicit, including none.");

  return errors;
}

module.exports = async ({ github, context, core }) => {
  const { owner, repo } = context.repo;

  if (context.eventName === "issues") {
    const issue = context.payload.issue;
    const result = await validateIssue({ github, owner, repo, issue, commentOnInvalid: true });
    if (!result.valid) core.setFailed(result.errors.join(" "));
    return;
  }

  if (context.eventName === "pull_request") {
    const errors = validatePullRequest(context.payload.pull_request.body || "");
    if (errors.length) core.setFailed(errors.join(" "));
    return;
  }

  let invalid = 0;
  const issues = await github.paginate(github.rest.issues.listForRepo, {
    owner,
    repo,
    state: "open",
    per_page: 100,
  });

  for (const issue of issues) {
    if (issue.pull_request) continue;
    const result = await validateIssue({ github, owner, repo, issue, commentOnInvalid: false });
    if (!result.valid) invalid += 1;
  }

  if (invalid) core.warning(`${invalid} open issue(s) do not satisfy the repository work metadata contract; they were marked invalid for repair.`);
};
