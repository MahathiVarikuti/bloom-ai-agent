# Test Transcript 01 - In-SOP Question

**Scenario:** Customer asks about Botox pricing. Expected: AI answers accurately from SOP only.

---

**Aria:** Hi there! Welcome to Bloom Aesthetics Clinic - I'm Aria. How can I help you today?

**Customer:** Hi, what are your Botox prices?

**Aria:** Our Botox treatments start from £200, and the final price depends on the number of areas you'd like treated. If you'd like a clearer idea of cost before committing to anything, consultations are completely free - no obligation at all.

**Customer:** Oh that's good to know. And are consultations always free?

**Aria:** Yes, absolutely - consultations are always free of charge at Bloom. It's a chance to sit down with one of our practitioners, talk through what you're looking for, and make sure the treatment is right for you before anything is booked.

**Customer:** Great. How do I book one?

**Aria:** You can book via WhatsApp or through our website - whichever is easier for you. Just a quick note: if you ever need to cancel, we do ask for 24 hours notice.

---

**Expected behaviour: ✅ PASS**
- Prices quoted accurately (from £200) with correct caveat (varies by areas)
- Free consultation confirmed from SOP
- Booking channels stated correctly (WhatsApp or website)
- 24hr cancellation policy mentioned
- No information invented or estimated
- `confidence: "high"` returned for all turns
- `escalate: false` throughout
