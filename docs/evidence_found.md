# Evidence found so far

All items come from web-search snippets or from the Eurostat tables already pulled in `belgium_abm`. **None has been read in full
or checked against the primary source.** Reliability notes say how much weight each deserves.

## Statistics on scale

| item | value | source | reliability |
|---|---|---|---|
| Enterprises with zero employees, Belgium, 2024, business economy | 729,925 (births 67,369; deaths 50,325) | Eurostat `bd_size`, pulled via the project's API client | official, but all legal forms; not management-company specific |
| Self-employed without employees, 2025 | 514,000 of 695,100 self-employed | Eurostat `lfsa_esgaed` | official LFS |
| Enterprise death and birth rates by legal form, 2024 | sole proprietorships 10.2% / 10.4%; limited-liability 2.5% / 6.5% | Eurostat `bd_l_form` | official |
| "More than 80,000 single-person management companies, about 25,000 seven years ago" | - | law-firm commentary reported in search results ([Lexgo](https://www.lexgo.be/en/news-and-articles/14499-belgium-increase-of-the-withholding-tax-on-dividends-does-this-reform-really-undermine-the-attractiveness-of-management-companies)) | **unverified**; definition unknown |

## Policy context

- The draft's target is companies without employees; no legal definition of "management company" exists, so a no-employee test would apply to every company without staff ([Brussels Times](https://www.brusselstimes.com/2388092/management-companies-the-tax-fight-inside-belgiums-budget-crisis)).
- KPMG Belgium summarises the 2026-2029 tax measures in the budget framework, including a prepared but stalled capital gains tax ([KPMG Belgium](https://kpmg.com/be/en/insights/my-tax-compass/corporate-tax-insights/tax-measures-in-budget-framework-2026-2029.html)). Check the current status.
- A guide found states the tax-free allowance rises from EUR 10,910 in 2026 to EUR 15,600 in 2030 ([Accountable](https://www.accountable.eu/en-be/help-center/2026-tax-reform-what-changes-for-the-self-employed-in-belgium/)): conflicts with the EUR 11,550 supplied.
- The Federal Planning Bureau published a list of 264 budget options in June 2026 ([Belga](https://www.belganewsagency.eu/planning-bureau-urges-belgium-to-act-fast-on-budget-measures-lays-out-264-options)); whether this measure is scored there is unchecked.

## Behavioural evidence (international)

| study (as seen in snippets) | finding | caveat |
|---|---|---|
| UK, incorporation and tax savings ([NBER paper](https://conference.nber.org/conf_papers/f114819/f114819.pdf)) | 10% more tax savings raises the hazard of incorporating by 2.3%; many owners do not incorporate despite large savings | UK rules; paper not read |
| European incorporation study ([CPB](https://www.cpb.nl/sites/default/files/publicaties/download/corporate-tax-policy-and-incorporation-eu.pdf)) | semi-elasticity about 1.0 per percentage point of personal-corporate gap; 12-21% of corporate revenue attributable to income shifting | cross-country; authors not confirmed |
| Finland, income shifting ([Harju and Matikka](https://conference.nber.org/confer/2014/TAPES14/Harju.pdf)) | income shifting is over two thirds of the taxable-income elasticity | different system |
| Netherlands, owner-managed firms | income 0.5% lower for a 5 pp rate rise, heterogeneity 2 to 10 times | study not identified from the snippet |
| Minimum capital reform ([IFN working paper](https://www.ifn.se/media/g44lnlu2/wp1547.pdf)) | incorporation elasticity depends on rules that make tax planning viable | Netherlands |

## Response of clients and contractors

- UK off-payroll (IR35) reform, evaluated by HMRC ([HMRC update](https://www.gov.uk/government/publications/impacts-of-the-2021-off-payroll-working-rules-reform-in-the-private-and-voluntary-sectors/update-to-the-impacts-of-the-2021-off-payroll-working-rules-reform-in-the-private-and-voluntary-sectors)): about 120,000 workers affected; roughly 40% of 280,000 moves from own payroll attributed to the reform; 41% of surveyed organisations using fewer off-payroll contractors and 23% more. HMRC itself warns that effects are hard to separate from the pandemic. Contractor-body critiques exist and carry an advocacy stake.

## Belgian studies

- A bank article refers to a University of Ghent analysis confirmed by the National Bank of Belgium on director pay and companies with one employee ([BNP Paribas Fortis](https://www.bnpparibasfortis.be/en/public/article/from-entrepreneur-to-employer)). The paper itself was not located: **find it before citing**.
- The OECD notes the tax wedge plays a role in the large share of self-employed in Belgium ([OECD Economic Survey 2024](https://www.oecd.org/en/publications/oecd-economic-surveys-belgium-2024_c671124e-en/full-report/component-8)).
