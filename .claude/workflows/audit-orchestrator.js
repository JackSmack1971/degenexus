/**
 * Deterministic architecture-audit orchestration for Claude Code-compatible runners.
 *
 * The workflow keeps the read-only AST audit separate from any subsequent
 * implementation pass. Runners are expected to provide an `agent` facade with a
 * `spawn(name, options)` method that returns `{ exitCode, stdout }`.
 */
export async function run(agent) {
  const auditResult = await agent.spawn('arch-audit-framework', { effort: 'high' });

  if (auditResult.exitCode === 0) {
    return agent.spawn('security-reviewer', { context: auditResult.stdout });
  }

  throw new Error('Initial AST Audit Failed.');
}
