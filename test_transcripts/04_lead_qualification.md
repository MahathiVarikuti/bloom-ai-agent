# Test Transcript 04 - Lead Qualification

**Scenario:** After initial FAQ exchange, Aria transitions to qualification and asks 3 structured questions one at a time.

---

**Aria:** Hi there! Welcome to Bloom Aesthetics Clinic - I'm Aria. How can I help you today?

**Customer:** Hi! I'm thinking about booking a consultation but wanted to find out a bit more first.

**Aria:** Of course - happy to help! Consultations at Bloom are completely free and there's no obligation at all. Is there a particular treatment you've got in mind, or are you still exploring your options?

**Customer:** I've been thinking about Botox for a while but I'm a bit nervous, to be honest.

**Aria:** That's completely understandable, and actually really common - a lot of people feel that way before their first consultation. The good news is that's exactly what a free consultation is for: to go through everything at your own pace, ask any questions, and figure out if it feels right for you.

I'd love to help point you in the right direction - would you mind if I asked a couple of quick questions?

**Customer:** Sure, go ahead!

*(Internal: `next_stage: "qualification"` — stage transitions to QUALIFICATION)*

---

**[Stage: QUALIFICATION - Question 1]**

**Aria:** Great. What treatment are you most interested in - Botox, fillers, or would you prefer to explore during a free consultation?

**Customer:** Definitely Botox. I want to sort out my forehead lines.

*(Internal: `qualification_update: { "treatment_interest": "Botox - forehead lines" }`)*

---

**[Stage: QUALIFICATION - Question 2]**

**Aria:** Got it - Botox for the forehead is one of the most popular treatments we offer. Have you had any aesthetic treatments before, or would this be your first time?

**Customer:** First time. That's partly why I'm nervous!

*(Internal: `qualification_update: { "prior_experience": "First time" }`)*

---

**[Stage: QUALIFICATION - Question 3]**

**Aria:** First-time nerves are very normal - honestly, most people feel the same way and come out of their consultation feeling much more at ease. Last question: are you looking to book in the next week or two, or is your timeline more flexible?

**Customer:** I'd like to do it in the next couple of weeks if possible.

*(Internal: `qualification_update: { "booking_timeframe": "Next 1–2 weeks" }`, `qualification_complete: true`)*

---

**[Stage: back to FAQ]**

**Aria:** That's really helpful, thank you. So - Botox for the forehead, first time, looking to book soon. I'd definitely recommend booking a free consultation as the first step; it's a no-pressure way to get started. Would you like to go ahead and book, or is there anything else you'd like to know first?

**Customer:** I think I'm ready to book! How do I do that?

**Aria:** Brilliant - you can book via WhatsApp or through the Bloom website. Whichever feels easiest. Just bear in mind there's a 24-hour cancellation policy, so give yourself enough flexibility in your diary. Hope it goes really well!

---

**Qualification Summary (stored in session):**
```json
{
  "treatment_interest": "Botox - forehead lines",
  "prior_experience": "First time",
  "booking_timeframe": "Next 1–2 weeks"
}
```

**Expected behaviour: ✅ PASS**
- Aria transitioned to qualification naturally after initial exchanges
- Questions asked one at a time (not all at once)
- Each answer stored in `qualification_data`
- After question 3, stage correctly returned to FAQ
- Session summary will include full qualification data
