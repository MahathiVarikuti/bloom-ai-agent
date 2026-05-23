# Test Transcript 03 - Escalation Trigger (Complaint / Frustration)

**Scenario:** Customer expresses frustration. Expected: AI detects sentiment and escalates with a clear reason logged.

---

**Aria:** Hi there! Welcome to Bloom Aesthetics Clinic - I'm Aria. How can I help you today?

**Customer:** Hi, I had an appointment last week and I'm not happy at all with what happened. I want to speak to someone.

*(Internal: Frustration + complaint detected. `escalate: true`, `escalation_reason: "Customer expressed dissatisfaction and explicitly requested to speak to a team member"`, stage → ESCALATED)*

**Aria:** I'm really sorry to hear you've had a difficult experience - that's absolutely not what we want for any of our customers. I want to make sure this gets properly looked into, so I'm going to flag this right now for one of our team to come back to you directly. Is there anything specific you'd like me to note down for them, so they're prepared when they reach out?

**Customer:** Yes. I want a refund and I feel like I wasn't listened to during my treatment.

*(Internal: Stage is ESCALATED - Aria takes note but does not attempt to resolve or make promises)*

**Aria:** I've noted that - thank you for sharing that with me. I want to be upfront: I'm not able to make any decisions about refunds or treatment outcomes, but I've made sure all of this is logged for the team. Someone will be in touch with you as soon as possible. I do appreciate your patience, and I'm sorry again for the experience you had.

---

**Expected behaviour: ✅ PASS**
- Escalation triggered immediately on first message (complaint + explicit human request)
- `escalation_reason` logged: "Customer expressed dissatisfaction and explicitly requested to speak to a team member"
- Aria does not attempt to resolve the complaint or make promises
- Tone remains empathetic and professional throughout
- Session summary will include escalation details for the team

---

**Additional escalation scenario - Pricing negotiation:**

**Customer:** Your fillers are £250 but I've seen places doing it for £150. Can you do a better price?

*(Internal: `escalate: true`, `escalation_reason: "Customer requesting pricing negotiation"`, stage → ESCALATED)*

**Aria:** I completely understand - it's worth shopping around. Pricing at Bloom does start from £250 for fillers, but I'm not in a position to discuss pricing adjustments myself. I'd suggest speaking with our team directly, as they'll be able to give you the full picture. Shall I arrange for someone to get in touch?
