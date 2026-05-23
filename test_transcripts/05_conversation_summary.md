# Test Transcript 05 - Conversation Summary

**Scenario:** Full session ending with `quit` command. Aria generates a structured summary covering intent, collected data, SOP gaps, and recommended next action.

---

*(Full conversation - abbreviated for readability)*

**Aria:** Hi there! Welcome to Bloom Aesthetics Clinic - I'm Aria. How can I help you today?

**Customer:** Hi, I'd like to know about fillers for my lips.

**Aria:** Of course! Dermal fillers start from £250 at Bloom, and the price varies depending on the type of filler and the amount used. If you'd like a more precise quote, a free consultation is a great first step - no commitment needed.

**Customer:** Do you do any numbing before the treatment?

**Aria:** That's a really common question, but I don't have details about the specific techniques used during treatment. That would be a brilliant thing to ask during a free consultation - the practitioner can walk you through exactly what to expect. Shall I flag that question for the team?

*(Internal: `sop_gap: "Customer asked about numbing/anaesthetic during filler treatment - not in SOP"`, `confidence: "low"`)*

**Customer:** What days are you open?

**Aria:** We're open Monday to Saturday, 9 AM to 7 PM. We're closed on Sundays.

**Customer:** That works. I'd love to book for next week.

**Aria:** Brilliant timing. You can book via WhatsApp or through our website - just remember there's a 24-hour cancellation policy. Would you like me to ask a couple of quick questions to help the team prepare for your visit?

**Customer:** Yes sure.

*(Qualification flow completes - see transcript 04 for full detail)*

*(Customer types: `quit`)*

---

## Generated Summary Output

```json
{
  "customer_intent": "Customer is interested in lip filler treatment and wants to book an appointment for the following week.",
  "key_details": {
    "services_enquired_about": ["Dermal Fillers (lips)"],
    "booking_intent": "high",
    "treatment_experience": "unknown"
  },
  "qualification_summary": {
    "treatment_interest": "Lip fillers",
    "prior_experience": "Not captured in this session",
    "booking_timeframe": "Next week"
  },
  "sop_gaps_identified": [
    "Customer asked about numbing/anaesthetic during filler treatment - not covered in SOP"
  ],
  "escalation": {
    "was_escalated": false,
    "reason": null,
    "trigger_message": null
  },
  "recommended_next_action": "Follow up with customer to confirm appointment booking for next week. Address their question about numbing/anaesthetic before the appointment - add this to the SOP for future reference."
}
```

---

**CLI Output (as shown in terminal):**

```
⚡ Wrapping up - generating session summary...

════════════════════════════════════════════════════
             SESSION SUMMARY
════════════════════════════════════════════════════

Customer Intent
  Customer is interested in lip filler treatment and wants to book an appointment for the following week.

Key Details
  Services Enquired About: Dermal Fillers (lips)
  Booking Intent: high
  Treatment Experience: unknown

Qualification Data
  Treatment Interest: Lip fillers
  Booking Timeframe: Next week

SOP Gaps Identified
  • Customer asked about numbing/anaesthetic during filler treatment - not covered in SOP

Recommended Next Action
  Follow up with customer to confirm appointment booking for next week. Address their question about numbing/anaesthetic before the appointment - add this to the SOP for future reference.

════════════════════════════════════════════════════

⚡ Session log saved → logs/session_20250115_143022.json
```

---

**Expected behaviour: ✅ PASS**
- Summary generated via separate dedicated API call (not the conversation prompt)
- All sections populated correctly from session data
- SOP gap surfaced and included in recommended next action
- No escalation recorded (correct - none was triggered)
- Recommended next action is specific and actionable, not generic
