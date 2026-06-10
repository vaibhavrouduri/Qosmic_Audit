# WORKFLOWS.md

I use coding agents most when the task can be made into a clear workflow: define the goal, give the agent constraints, let it act inside the repo, and check the output with logs or tests. I do not treat agents as something that should freely design the whole system. I get the most value when I can give them a bounded part of the work and a clear definition of done.

A pattern I have used before is a controller-agent loop. In my ML for Cybersecurity lab, my team built a CTF solver where the LLM was the planner, not the executor. The model had to output a strict JSON action, and a local controller ran the command, captured stdout/stderr, enforced timeouts and step limits, and sent the result back to the model. That made the agent useful for exploration, but the actual side effects were still controlled by our code.

I have also used Gemini CLI in hackathon-style builds. In those cases, I usually define the architecture and acceptance criteria first, then use the agent to implement pieces faster, debug errors, and connect parts of the app. One example was a game where an LLM acted as the judge inside the product, while Gemini CLI helped build parts of the surrounding app.

My delegation pattern is: I decide what the system should do, what the boundaries are, and how I will know it is correct. Then I let the agent implement scoped pieces. I am comfortable giving agents tasks like writing scripts, converting a workflow into code, adding validation, debugging a specific error, refactoring, or generating a first pass from well-defined inputs.

I do not fully hand over open-ended design or final judgment. If the output can sound right without being testable, I do not trust it directly. I review it, run it, check the logs, and then tighten the prompt or the code if needed.

One thing I want to improve is planning the full system shape before building each piece. In this project, I sometimes optimized one part at a time, then had to work around decisions that were already baked into the rest of the flow. For example, once `AGENTS.md` became the main workflow contract, changes to it had to be made carefully because the crawler, report generation, eval loop, and human feedback flow all depended on it. I also made the evaluator very strong early, which made human feedback more important than I initially expected. I should map the full loop earlier so each component is optimized for the system, not just locally good.


