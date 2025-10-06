# Licensing Guide

Agent Forge is available under a dual-license model. You can choose between:

1. **GNU Affero General Public License v3.0 (AGPLv3)** — best for open source usage.
2. **Agent Forge Commercial License** — best for closed-source or proprietary deployment.

This guide helps you pick the right option and explains the obligations that come with each license.

---

## Quick Decision Matrix

| Scenario | Recommended License | Key Obligations |
|----------|--------------------|-----------------|
| Building an open platform and happy to share improvements | **AGPLv3** | Share source code of modifications, keep network-facing changes open |
| Integrating Agent Forge into a SaaS product where source must remain private | **Commercial License** | Pay annual fee, follow commercial terms |
| Evaluating Agent Forge internally without exposing it to external users | **AGPLv3** | No redistribution obligations if not accessible over a network |
| OEM/ISV distributing Agent Forge to customers inside a proprietary product | **Commercial License** | Pay annual fee, provide attribution |

---

## License Summaries

### AGPLv3 (Free & Open Source)

- Guarantees the four freedoms: run, study, modify, share.
- Requires that if you modify Agent Forge and make it available to users over a network, you must provide the complete source code of your modified version.
- Compatible with other strong copyleft licenses.
- Ideal for community contributions, research projects, and organizations committed to open source.

### Commercial License (Paid, Proprietary-Friendly)

- Grants rights to keep derivative works closed-source.
- Includes commercial support options and flexibility around redistribution.
- Requires annual licensing fee (see `COMMERCIAL-LICENSE.md`).
- Ideal for startups, enterprises, and SaaS vendors who need to protect proprietary integrations or business logic.

---

## Choosing the Right License

1. **Are you planning to distribute or host Agent Forge as part of a service where users interact with it over a network?**
   - **Yes** → You must comply with AGPLv3 or obtain a commercial license.
2. **Do you need to keep your modifications private?**
   - **Yes** → Select the commercial license.
   - **No** → AGPLv3 may be sufficient.
3. **Do you require official support, SLAs, or custom integrations?**
   - **Yes** → Commercial license recommended.
4. **Do you contribute fixes or features back to the community?**
   - **Yes** → AGPLv3 is a natural fit.

---

## Compliance Checklist

### If You Choose AGPLv3

- [ ] Provide access to the full source code of any modified version running in production.
- [ ] Include a copy of the AGPLv3 license in your distribution (`LICENSE`).
- [ ] Preserve copyright notices and attribution.
- [ ] Document significant changes in `CHANGELOG.md` or similar file.
- [ ] Make sure all dependencies are compliant with AGPLv3 terms.

### If You Choose the Commercial License

- [ ] Sign or accept the Agent Forge Commercial License agreement.
- [ ] Pay the annual licensing fee according to your tier.
- [ ] Keep a copy of your executed order form/invoice for audit purposes.
- [ ] Include the required attribution: `Powered by Agent Forge — © 2025 m0nk111`.
- [ ] Restrict access to the source code to authorized personnel only.

---

## Frequently Asked Questions

**Q: Can I start under AGPLv3 and later switch to the commercial license?**  
A: Yes. Contact us at `licensing@m0nk111.dev` to transition. Past compliance with AGPLv3 must be preserved for the time you operated under it.

**Q: Does the commercial license cover multiple products?**  
A: The default tiers cover the specified number of products. Enterprise contracts can be customized.

**Q: What if I only run Agent Forge internally?**  
A: If no external users access the software over a network, the AGPLv3 does not obligate you to share your modifications. Once external users interact with your modified instance, the sharing obligation applies.

**Q: Can I combine AGPLv3 components with proprietary modules?**  
A: Yes, as long as the AGPL-covered parts remain compliant. Boundary integration via APIs is often used to keep proprietary modules separate.

**Q: Is there a contributor license agreement (CLA)?**  
A: Currently no CLA is required. Contributions are accepted under AGPLv3 plus a re-license grant to the commercial offering.

---

## Contact

- **Email**: licensing@m0nk111.dev
- **Website**: https://agent-forge.m0nk111.dev/licensing
- **Commercial License**: See `COMMERCIAL-LICENSE.md`
- **Open Source License**: See `LICENSE`

---

_This document will evolve as the licensing program expands. Please propose updates via pull request or contact the maintainers._
