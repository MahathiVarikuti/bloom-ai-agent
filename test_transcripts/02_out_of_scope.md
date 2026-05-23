# Test Transcript 02 - Out-of-Scope Question

**Scenario:** Customer asks something the SOP doesn't cover. Expected: AI acknowledges the gap honestly and offers to escalate, rather than guessing.

---

**Aria:** Hi there! Welcome to Bloom Aesthetics Clinic - I'm Aria. How can I help you today?

**Customer:** Hi, do you offer lip blushing or semi-permanent makeup?

**Aria:** That's a great question - I don't have details about lip blushing or semi-permanent makeup in the information I have to hand right now. I wouldn't want to give you the wrong answer, so it might be best to check with the team directly - shall I flag that for you, or would you like to reach out via WhatsApp?

*(Internal: `confidence: "low"`, `sop_gap: "Customer asked about lip blushing / semi-permanent makeup - not covered in SOP"`, `escalate: false`)*

**Customer:** Okay. Do you have a Groupon or any discount packages?

**Aria:** I'm afraid I don't have information about discount packages or promotional deals - that's something our team would be better placed to answer. Would you like me to flag both questions so someone can come back to you with the full picture?

*(Internal: `confidence: "low"`, `sop_gap: "Customer asked about Groupon / discount packages - not in SOP"`, consecutive unanswered = 2)*

**Aria:** Actually, since I've not been able to answer a couple of your questions, let me make sure you get the right help - I'll flag this for the team and someone will be in touch shortly.

*(Internal: `escalate: true`, `escalation_reason: "Two consecutive questions outside SOP scope"`, stage → ESCALATED)*

---

**Expected behaviour: ✅ PASS**
- First unanswered question: Aria is honest, doesn't guess, offers to flag it
- Second consecutive unanswered question: automatic escalation triggered
- `sop_gap` logged for both questions (fed into session summary)
- Customer is never given made-up information
- Tone stays warm and helpful, not defensive
