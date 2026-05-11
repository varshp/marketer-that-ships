## Reddit Signal Report: r/msp

### Top recurring complaints

1. **Ingram Micro is in crisis post-hack** — Multiple posts and comments describe billing errors, fulfillment delays, degraded customer service, broken web portals, and mysterious account balances. One user accumulated $65K in charges on a credit-card-only account without being notified. Another notes "Post hack, they suspended our Dropbox Subscriptions across random tenants twice. No reason, no sorry, no nothing." A European user adds: "everything went to shit after they launched their new website. Slow as hell, filtering doesn't work."

2. **OEM/vendor field technicians are shockingly incompetent** — Dell subcontracts through Unisys/Field Nation/WorkMarket, and MSPs are routinely forced to hand-hold or clean up after them. One user "wrote an entire internal KB for our team on how to address Dell technicians being useless." Another had a Dell rep "destroy a laptop because they didn't know how to take the keyboard out."

3. **Checkpoint/Avanan DKIM breakage requiring paid fix** — Checkpoint's inline email scanning breaks DKIM signatures, causing DMARC failures. Users are frustrated that the "fix" is a paid add-on: "Shouldn't have to buy this add on to fix the signing bug." One commenter frames it sharply: "you're still paying for a fix to a problem their own product creates."

4. **Deceptive vendor sales tactics** — Koja Analytics and similar vendors disguise sales calls as inbound leads to get callbacks. MSPs are furious: "They called our projects line, made it sound like a customer looking for services. Waste of my time." The community wants a pinned "shitty vendor marketing megathread."

5. **Inherited junk hardware from previous MSPs** — Araknis networking gear (sold through AV/smart-home channels) is universally condemned. "Replace it — do not pass go, do not spend any time on it." MSPs repeatedly burn onboarding hours troubleshooting gear they didn't choose and can't access.

6. **Threat reports are repetitive and unhelpful** — The ConnectWise 2026 MSP Threat Report is seen as recycled content: "I'm pretty sure this could just have been the same report verbatim for the last 2 or 3 years." MSPs crave actionable, novel intelligence, not marketing-gated PDFs.

7. **Shadow AI / ungoverned AI tool usage** — MSPs are seeing users on ChatGPT, Claude, etc. with "no control over these tools, other than outright blocking." There's anxiety about data leakage and no consensus on the right approach.

### Top recurring praise

1. **TD Synnex and D&H praised as reliable distributors** — "TD Synnex is at the top." D&H gets orders delivered faster and cheaper than Ingram on identical Dell laptop orders.

2. **Veeam hardened repos and repurposed Datto hardware** — Community actively shares knowledge on repurposing Datto appliances for Veeam or TrueNAS. Collaborative spirit is strong, including sharing BIOS passwords ("R@str — works for most units up to the Siris 4").

3. **CIS Benchmarks for security configuration** — When someone posts a custom Entra P1 SOP, the community immediately points to CIS Microsoft 365 Benchmarks as the gold standard, suggesting strong trust in established frameworks.

4. **Copilot within the Microsoft ecosystem as the "approved lane" for AI** — Users praise the approach of pushing AI usage into Copilot/Microsoft tenant where data governance is possible: "Within copilot studio you can essentially recreate anything Claude can do all within the M365 ecosystem."

5. **Answering the phone and communicating well** — The most upvoted differentiator isn't technology; it's responsiveness: "Answer the phone and email promptly. Seriously. Amazing how many don't."

6. **SMB1001 certification for small business clients** — "I get all clients gold certified. They love it. For small business 5 to 50 this is a great starting point to kick-start their journey to ISO."

7. **DNSFilter for AI usage visibility** — Called out specifically as providing reporting on which AI tools users are accessing.

### Exact Reddit language

- "stuck in the mud" (describing MSPs in the 8-25 person range)
- "rip and replace" (unanimous recommendation for bad inherited gear)
- "Shadow AI" (ungoverned AI tool usage by end users)
- "the doordash of technicians" (describing Dell's subcontracted Unisys field techs)
- "do not pass go, do not spend any time on it"
- "It's the IBM of distributors...shit." (describing Ingram Micro)
- "Sir you did not do the needful"
- "coaches quietly call when their clients are on fire"
- "If any of it is eye-opening, you are way behind the curve"
- "Why are you even answering your phone in 2026?"
- "What do I press if I am deceased?"
- "Uninstalled a full Araknis network legit yesterday. It's wack"
- "you aren't important enough to get a phonecall from a company"
- "the basics haven't changed. Patch, MFA, backups, EDR."
- "Outright blocking just creates Shadow AI"
- "the expensive part with incidents like that is not the five minutes of outage, it's how fast the trail goes cold afterward"
- "shitty vendor marketing megathread with a running list of violators"
- "more likey profit like av company profit vs stability"

### Questions nobody is answering well

1. **How to build a practical AI governance framework for MSP clients** — Everyone agrees "just blocking" is wrong and "Shadow AI" is the risk, but nobody has a concrete, replicable policy template or toolchain beyond "push them into Copilot." The question of what data can go into which tools remains unanswered.

2. **What actually differentiates an MSP beyond "communication and SOPs"?** — The original question about unique services gets philosophical answers about process and people, but very few concrete, lesser-known service offerings that create competitive moats. Dark web monitoring, session cookie theft protection, and Shodan-style services are mentioned by OP but not substantively discussed.

3. **How to properly investigate brief, transient SSL/certificate interception events** — The Huawei cert SSL error post gets speculative answers (DNS hijack, ISP transparent proxy, SD-WAN failover) but no one provides a definitive forensic workflow for when "the trail goes cold" in 5 minutes.

4. **How to handle inherited vendor billing disputes at scale** — Multiple Ingram Micro billing horror stories, but no one shares a proven escalation path, legal leverage, or systematic audit process. It's all "demand a full ledger" without specifics.

5. **Repurposing Datto hardware for non-Datto backup solutions** — Several people confirm it works, but detailed guides on firmware, compatibility, and performance benchmarks for specific Datto models running Rocky Linux / Veeam hardened repos are missing.

6. **Entra P1 security configuration best practices vs. CIS benchmarks** — Someone posts their custom SOP and gets a one-line redirect to CIS benchmarks. No discussion of where CIS falls short, what's P1-specific vs. P2, or real-world implementation gotchas.

### Emerging themes

1. **AI governance as a new MSP service line** — The conversation is shifting from "should we block AI" to "how do we offer governed AI access as a managed service." Copilot + Copilot Studio + Anthropic models within EDP are becoming the "approved stack." This is quickly becoming a differentiator conversation.

2. **Distributor instability reshaping purchasing behavior** — The Ingram Micro post-hack fallout is pushing MSPs to diversify or consolidate with D&H and TD Synnex. Trust erosion is real and accelerating. "AI-driven order fulfillment" rumors at Ingram are adding anxiety.

3. **Session-layer and identity attacks eclipsing endpoint threats** — Multiple references to Evilginx, session cookie stealing, OTP bypass, and phishing-resistant MFA. The community recognizes that traditional MFA is insufficient but practical deployment guidance is thin.

4. **MSP-to-MSP knowledge sharing on vendor workarounds** — The community is building its own shadow documentation: internal KBs for handling bad Dell techs, shared BIOS passwords for Datto devices, direct PDF links to bypass gated vendor reports. This is a trust signal — MSPs trust peers over vendors.

5. **Growing hostility toward vendor marketing practices** — Disguised sales calls, gated threat reports, and paid fixes for vendor-created bugs are creating a backlash. There's demand for a community-maintained "vendor blacklist."

6. **Zero-day exploitation velocity outpacing SMB patching cadence** — The conversation around the Adobe Reader zero-day and Claude Mythos finding a 27-year-old OpenBSD bug signals awareness that "the gap between how fast zero days are now being found and how fast the average SMB patches" is the real emerging risk.

### PMM action items

1. **If you sell a distributor alternative or procurement platform**: Lead with the Ingram Micro pain. Use exact language: "billing holds on your account for problems that aren't yours" and "fulfillment that takes days while D&H ships overnight." Create a migration guide specifically for MSPs leaving Ingram post-hack.

2. **If you sell AI governance or DLP tools**: Position around "Shadow AI" explicitly — the community already uses this term. Build messaging around "governed access, not blocked access" and show how your tool provides visibility into what data users are feeding into which AI tools. A one-page "AI Acceptable Use Policy" template would generate massive goodwill.

3. **If you sell email security**: Do NOT break DKIM. The Checkpoint/Avanan backlash is a direct competitive opening. Messaging should explicitly say: "We don't charge you to fix problems we create. DKIM integrity preserved, no add-ons required." This is a switchable moment.

4. **If you sell to MSPs, stop disguising sales calls as leads and stop gating basic reports.** The community is actively building blacklists. Instead, earn trust by providing ungated resources and transparent outreach. One user literally posted a direct PDF link to bypass ConnectWise's gate and was celebrated for it.

5. **If you sell networking hardware**: Create an explicit "Araknis Rip and Replace" program or migration guide. The community consensus is universal — "replace it with literally anything." Position your product as the obvious upgrade path with a fast-onboarding story for MSPs inheriting bad client networks.

6. **If you sell security configuration or compliance tools**: Build around CIS benchmarks as the baseline (the community already trusts them), but differentiate by showing where CIS falls short for specific license tiers (P1 vs. P2) and providing implementation automation, not just checklists.

7. **If you sell backup/BCDR**: Lean into the Datto-to-Veeam migration narrative. The community is actively repurposing hardware. Provide certified compatibility guides for Datto appliance models running your software, and make the migration path frictionless. Axcient is already doing this ("they like to help you repurpose Dattos") — match or beat that play.

8. **For any vendor marketing to MSPs**: Adopt a peer-voice tone, not a vendor tone. The most trusted voices in this community speak in blunt, practical, slightly irreverent language. Avoid polished corporate messaging. Use phrases like "rip and replace," reference real tools by name, and acknowledge known industry problems openly rather than pretending they don't exist.