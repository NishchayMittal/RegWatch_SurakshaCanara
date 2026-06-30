
-- RegWatch — Seed Data
-- Canara Bank Regulatory Compliance Pipeline
-- Run after schema.sql



-- 1. DEPARTMENTS (9 rows)


INSERT INTO departments (name, description, contact_email, slack_webhook) VALUES
(
    'Treasury & Investments',
    'Manages CRR, SLR, LCR, NSFR, bond portfolio, forex operations, ALM, and Basel III capital compliance. Primary point of contact for all RBI monetary policy and liquidity directives.',
    'treasury.compliance@canarabank.com',
    'https://hooks.slack.com/mock/treasury'
),
(
    'KYC / AML',
    'Owns all Know Your Customer, Anti-Money Laundering, and PMLA obligations. Handles STR/CTR filing with FIU-IND, PEP screening, CKYC registry, and Video KYC implementation.',
    'kyc.aml@canarabank.com',
    'https://hooks.slack.com/mock/kyc-aml'
),
(
    'Credit Risk',
    'Responsible for NPA classification, provisioning norms (IRAC), stressed asset resolution, large exposure framework, priority sector lending targets, and Ind AS 109 ECL provisioning.',
    'creditrisk.compliance@canarabank.com',
    'https://hooks.slack.com/mock/credit-risk'
),
(
    'Retail Banking Compliance',
    'Covers fair lending practices, digital lending guidelines, credit card regulations, customer grievance redressal, Banking Ombudsman compliance, and financial inclusion mandates.',
    'retail.compliance@canarabank.com',
    'https://hooks.slack.com/mock/retail'
),
(
    'IT & Cybersecurity',
    'Handles RBI Cyber Security Framework, incident reporting to CSITE, BCP/DR testing, data localisation, SWIFT CSP compliance, cloud computing guidelines, and payment system security.',
    'ciso@canarabank.com',
    'https://hooks.slack.com/mock/it-cyber'
),
(
    'HR & Conduct',
    'Manages fit and proper criteria for directors, compensation and remuneration policy, whistleblower mechanism, insider trading code of conduct, staff certifications, and POSH compliance.',
    'hr.compliance@canarabank.com',
    'https://hooks.slack.com/mock/hr'
),
(
    'Legal & Regulatory Affairs',
    'Handles all regulatory filings, SEBI LODR disclosures, Companies Act MCA21 compliance, litigation management, board resolutions for compliance actions, and FEMA legal matters.',
    'legal.compliance@canarabank.com',
    'https://hooks.slack.com/mock/legal'
),
(
    'Trade Finance',
    'Owns letter of credit, bank guarantee, export/import finance, FEMA trade reporting, EDPMS/IDPMS compliance, authorised dealer obligations, and supply chain finance regulations.',
    'tradefinance.compliance@canarabank.com',
    'https://hooks.slack.com/mock/trade-finance'
),
(
    'Audit & Inspection',
    'Responsible for RBIA framework, RBI Annual Financial Inspection coordination, fraud detection and FMR reporting to RBI, LFAR preparation, IS audit, and compliance testing across all departments.',
    'audit.chief@canarabank.com',
    'https://hooks.slack.com/mock/audit'
);



-- 2. SLAs (9 departments × 3 regulators = 27 rows)
-- Realistic banking SLAs based on actual RBI/SEBI/MCA urgency


-- Treasury & Investments
-- RBI monetary directives are urgent (CRR changes effective next fortnight)
INSERT INTO slas (department_id, circular_source, days_to_complete) VALUES
(1, 'RBI',  7),
(1, 'SEBI', 14),
(1, 'MCA',  21);

-- KYC / AML
-- KYC drives take time — large customer base
INSERT INTO slas (department_id, circular_source, days_to_complete) VALUES
(2, 'RBI',  30),
(2, 'SEBI', 21),
(2, 'MCA',  30);

-- Credit Risk
-- NPA classification changes need immediate action
INSERT INTO slas (department_id, circular_source, days_to_complete) VALUES
(3, 'RBI',  14),
(3, 'SEBI', 21),
(3, 'MCA',  30);

-- Retail Banking Compliance
-- Customer-facing changes need fast turnaround
INSERT INTO slas (department_id, circular_source, days_to_complete) VALUES
(4, 'RBI',  21),
(4, 'SEBI', 14),
(4, 'MCA',  30);

-- IT & Cybersecurity
-- Cyber incidents and data localisation are urgent
INSERT INTO slas (department_id, circular_source, days_to_complete) VALUES
(5, 'RBI',  14),
(5, 'SEBI', 21),
(5, 'MCA',  21);

-- HR & Conduct
-- Policy updates need board approval — longer cycle
INSERT INTO slas (department_id, circular_source, days_to_complete) VALUES
(6, 'RBI',  30),
(6, 'SEBI', 21),
(6, 'MCA',  30);

-- Legal & Regulatory Affairs
-- Filing deadlines are fixed by law — tight SLAs
INSERT INTO slas (department_id, circular_source, days_to_complete) VALUES
(7, 'RBI',  14),
(7, 'SEBI', 7),
(7, 'MCA',  7);

-- Trade Finance
-- FEMA violations are serious — keep tight
INSERT INTO slas (department_id, circular_source, days_to_complete) VALUES
(8, 'RBI',  14),
(8, 'SEBI', 21),
(8, 'MCA',  30);

-- Audit & Inspection
-- Fraud reporting has legal deadlines (3 weeks for Rs 1cr+)
INSERT INTO slas (department_id, circular_source, days_to_complete) VALUES
(9, 'RBI',  21),
(9, 'SEBI', 21),
(9, 'MCA',  30);



-- 3. CIRCULARS (5 real-style circulars)
-- Mix of RBI, SEBI, MCA — different statuses


INSERT INTO circulars (
    source, title, url, raw_text, published_at, ingested_at, status, dedup_hash
) VALUES

-- Circular 1: processed — LCR reporting (Treasury)
(
    'RBI',
    'Liquidity Coverage Ratio (LCR) — Revision of Run-off Rates and Reporting Frequency',
    'https://rbi.org.in/Scripts/NotificationUser.aspx?Id=12601',
    'RBI/2024-25/47 DOR.LRG.REC.34/03.10.001/2024-25. Dear Sir/Madam, Liquidity Coverage Ratio (LCR) — Revision of Run-off Rates and Reporting Frequency. Please refer to our circular dated February 21, 2014 on "Basel III Framework on Liquidity Standards — Liquidity Coverage Ratio (LCR), Liquidity Risk Monitoring Tools and LCR Disclosure Standards." 1. Banks shall maintain a minimum LCR of 100% on an ongoing basis effective from [date]. 2. The run-off rate for stable retail deposits is revised from 5% to 7.5%. 3. Banks shall submit LCR returns on a daily basis within 5 working days of the end of each month in the format prescribed. 4. Recognised High Quality Liquid Assets (HQLA) shall be unencumbered and free from any legal, regulatory, contractual, or other restriction. 5. Banks shall put in place a Board-approved LCR policy by [compliance date]. Yours faithfully.',
    '2024-09-15 10:30:00',
    '2024-09-15 11:45:00',
    'processed',
    'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2'
),

-- Circular 2: processed — KYC periodic updation
(
    'RBI',
    'Master Direction on KYC — Amendments to Periodic Updation and Risk Categorisation',
    'https://rbi.org.in/Scripts/NotificationUser.aspx?Id=12589',
    'RBI/2024-25/31 DoR.AML.REC.22/14.01.001/2024-25. Dear Sir/Madam, Master Direction (MD) on Know Your Customer (KYC) — Amendment. In exercise of powers conferred under Sections 35A and 56 of the Banking Regulation Act 1949 and Rules 9 and 9A of the Prevention of Money Laundering (Maintenance of Records) Rules 2005, RBI hereby amends the Master Direction on KYC. 1. Periodic updation of KYC for existing customers: High Risk — every 2 years; Medium Risk — every 8 years; Low Risk — every 10 years. 2. All Regulated Entities (REs) shall implement a risk-based approach for customer categorisation by [date]. 3. REs shall file Suspicious Transaction Reports (STRs) with FIU-IND within 7 days. 4. Video based Customer Identification Process (V-CIP) shall be accepted as a valid KYC method for all account types. 5. REs shall submit a compliance certificate to their respective Regional Office of RBI within 90 days.',
    '2024-08-20 09:00:00',
    '2024-08-20 10:15:00',
    'processed',
    'b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3'
),

-- Circular 3: processed — Digital Lending (Retail)
(
    'RBI',
    'Digital Lending — Guidelines on Default Loss Guarantee and Key Fact Statement',
    'https://rbi.org.in/Scripts/NotificationUser.aspx?Id=12612',
    'RBI/2024-25/55 DoR.FIN.REC.41/03.10.136/2024-25. Dear Sir/Madam, Digital Lending — Amendments to Guidelines. Reference is invited to RBI Circular on Digital Lending dated September 2, 2022. 1. Regulated Entities (REs) shall provide a Key Fact Statement (KFS) to all borrowers before execution of the loan contract. The KFS shall contain Annual Percentage Rate (APR), all fees and charges, grievance redressal officer details, and cooling-off period. 2. Default Loss Guarantee (DLG) arrangements shall be disclosed to borrowers. DLG shall not exceed 5% of the loan portfolio outstanding at the beginning of each quarter. 3. All loan disbursements shall be made directly to the borrowers bank account. No disbursement to third-party wallets. 4. Recovery of loans shall be conducted only by REs or their authorised agents. 5. Each RE shall appoint a Nodal Grievance Redressal Officer at the senior management level by [date].',
    '2024-10-01 11:00:00',
    '2024-10-01 12:30:00',
    'processed',
    'c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4'
),

-- Circular 4: processed — SEBI LODR Corporate Governance
(
    'SEBI',
    'SEBI (Listing Obligations and Disclosure Requirements) — Amendments to Corporate Governance Norms',
    'https://sebi.gov.in/legal/circulars/oct-2024/amendment-lodr-corporate-governance_87432.html',
    'SEBI/HO/CFD/PoD-2/P/CIR/2024/131. Dear Sir/Madam, Sub: Amendments to SEBI (Listing Obligations and Disclosure Requirements) Regulations, 2015. 1. Listed entities shall submit quarterly compliance report on corporate governance within 21 days from end of each quarter signed by the Compliance Officer or CEO. 2. Board of Directors shall have at least one-third independent directors. For listed entities with a woman as Chairperson, at least one-third of the board shall be independent. 3. Audit Committee shall comprise at least two-thirds independent directors. 4. All material related party transactions shall be approved by shareholders via special resolution. Threshold for material RPT revised to lower of Rs. 1000 crore or 10% of annual turnover. 5. Listed entities shall maintain a vigil mechanism (whistleblower policy) and disclose it on the website. 6. The Compliance Officer shall be a Key Managerial Personnel (KMP). Compliance report must be filed with stock exchange within 21 days of each quarter end.',
    '2024-10-10 14:00:00',
    '2024-10-10 15:20:00',
    'processed',
    'd4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5'
),

-- Circular 5: processing — MCA Director KYC (just ingested)
(
    'MCA',
    'MCA21 — Mandatory Filing of DIR-3 KYC for All Directors by September 30',
    'https://mca.gov.in/content/mca/global/en/acts-rules/ebooks/circulars.html?act=MzQ1OQ==',
    'General Circular No. 08/2024. F.No. 01/01/2013-CL-V-Part-I. Government of India, Ministry of Corporate Affairs. Subject: Last date for filing DIR-3 KYC / DIR-3 KYC-Web without fee for the financial year 2023-24. All directors who have been allotted a Director Identification Number (DIN) on or before 31st March 2024 and whose DIN is in approved status are mandatorily required to file DIR-3 KYC or DIR-3 KYC-Web as the case may be. The last date for filing of e-form DIR-3 KYC or DIR-3 KYC Web on MCA21 portal for the financial year 2023-24 without fee is 30th September 2024. Directors who fail to file by this date will have their DIN marked as deactivated and will need to pay a fee of Rs. 5000 to reactivate. Companies shall ensure all their directors file DIR-3 KYC before the deadline.',
    '2024-09-01 09:00:00',
    '2024-09-01 10:00:00',
    'processing',
    'e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6'
);



-- 4. MAPs (12 action points across 5 circulars)
-- Mix of statuses to make the dashboard live


INSERT INTO maps (
    circular_id, map_text, source_paragraph, confidence_score, status,
    extracted_at, reviewed_at, reviewed_by
) VALUES

-- Circular 1 (LCR) — 3 MAPs, all assigned/in_progress (Treasury)
(
    1,
    'Maintain minimum LCR of 100% on an ongoing basis and revise run-off rate for stable retail deposits from 5% to 7.5% effective from the compliance date.',
    'Banks shall maintain a minimum LCR of 100% on an ongoing basis effective from [date]. The run-off rate for stable retail deposits is revised from 5% to 7.5%.',
    0.97,
    'in_progress',
    '2024-09-15 12:00:00',
    '2024-09-15 13:00:00',
    'auto_approved'
),
(
    1,
    'Submit LCR returns on a daily basis within 5 working days of end of each month in the prescribed format.',
    'Banks shall submit LCR returns on a daily basis within 5 working days of the end of each month in the format prescribed.',
    0.94,
    'completed',
    '2024-09-15 12:05:00',
    '2024-09-15 13:05:00',
    'auto_approved'
),
(
    1,
    'Put in place a Board-approved LCR policy by the compliance date specified in the circular.',
    'Banks shall put in place a Board-approved LCR policy by [compliance date].',
    0.91,
    'escalated',
    '2024-09-15 12:10:00',
    '2024-09-15 13:10:00',
    'auto_approved'
),

-- Circular 2 (KYC) — 3 MAPs, mix of completed and disputed
(
    2,
    'Implement risk-based customer categorisation: High Risk KYC updation every 2 years, Medium Risk every 8 years, Low Risk every 10 years.',
    'Periodic updation of KYC for existing customers: High Risk — every 2 years; Medium Risk — every 8 years; Low Risk — every 10 years.',
    0.98,
    'completed',
    '2024-08-20 11:00:00',
    '2024-08-20 12:00:00',
    'auto_approved'
),
(
    2,
    'File Suspicious Transaction Reports (STRs) with FIU-IND within 7 days of conclusion that a transaction is suspicious.',
    'REs shall file Suspicious Transaction Reports (STRs) with FIU-IND within 7 days.',
    0.96,
    'completed',
    '2024-08-20 11:05:00',
    '2024-08-20 12:05:00',
    'auto_approved'
),
(
    2,
    'Accept Video based Customer Identification Process (V-CIP) as valid KYC method for all account types and submit compliance certificate to RBI Regional Office within 90 days.',
    'Video based Customer Identification Process (V-CIP) shall be accepted as a valid KYC method for all account types. REs shall submit a compliance certificate within 90 days.',
    0.72,
    'disputed',
    '2024-08-20 11:10:00',
    '2024-08-20 14:00:00',
    'rajesh.kumar@canarabank.com'
),

-- Circular 3 (Digital Lending) — 2 MAPs
(
    3,
    'Provide Key Fact Statement (KFS) to all borrowers before loan execution containing APR, all fees, grievance officer details, and cooling-off period.',
    'REs shall provide a Key Fact Statement (KFS) to all borrowers before execution of the loan contract.',
    0.95,
    'in_progress',
    '2024-10-01 13:00:00',
    '2024-10-01 14:00:00',
    'auto_approved'
),
(
    3,
    'Appoint a Nodal Grievance Redressal Officer at senior management level by the compliance date and ensure all loan disbursements go directly to borrower bank accounts.',
    'Each RE shall appoint a Nodal Grievance Redressal Officer at the senior management level by [date].',
    0.88,
    'assigned',
    '2024-10-01 13:05:00',
    '2024-10-01 14:05:00',
    'auto_approved'
),

-- Circular 4 (SEBI LODR) — 2 MAPs, split between Legal and HR
(
    4,
    'Submit quarterly corporate governance compliance report to stock exchanges within 21 days of quarter end, signed by Compliance Officer or CEO.',
    'Listed entities shall submit quarterly compliance report on corporate governance within 21 days from end of each quarter.',
    0.96,
    'completed',
    '2024-10-10 16:00:00',
    '2024-10-10 17:00:00',
    'auto_approved'
),
(
    4,
    'Establish and disclose a whistleblower/vigil mechanism on the company website. Compliance Officer must be designated as a Key Managerial Personnel.',
    'Listed entities shall maintain a vigil mechanism and disclose it on the website. The Compliance Officer shall be a Key Managerial Personnel (KMP).',
    0.74,
    'pending_review',
    '2024-10-10 16:05:00',
    NULL,
    NULL
),

-- Circular 5 (MCA DIR-3) — 2 MAPs, just extracted, pending review
(
    5,
    'All directors with DIN allotted on or before 31st March 2024 must file DIR-3 KYC or DIR-3 KYC-Web on MCA21 portal before 30th September 2024.',
    'All directors who have been allotted a DIN on or before 31st March 2024 are mandatorily required to file DIR-3 KYC or DIR-3 KYC-Web.',
    0.93,
    'pending_review',
    '2024-09-01 11:00:00',
    NULL,
    NULL
),
(
    5,
    'Companies shall ensure all their directors complete DIR-3 KYC filing before the deadline to avoid DIN deactivation and Rs. 5000 reactivation fee.',
    'Companies shall ensure all their directors file DIR-3 KYC before the deadline.',
    0.89,
    'pending_review',
    '2024-09-01 11:05:00',
    NULL,
    NULL
);



-- 5. TASKS (assigned from MAPs to departments)


INSERT INTO tasks (
    map_id, department_id, assigned_at, due_at, completed_at, status, evidence_url, notes
) VALUES

-- MAP 1 (LCR 100% + run-off rate) → Treasury (dept 1), RBI SLA = 7 days
(1, 1, '2024-09-15 13:00:00', '2024-09-22 13:00:00', NULL,
 'in_progress', NULL,
 'Treasury team updating ALM system run-off rates. CBS change request raised.'),

-- MAP 2 (LCR returns daily) → Treasury (dept 1), already completed
(2, 1, '2024-09-15 13:05:00', '2024-09-22 13:05:00', '2024-09-20 10:00:00',
 'completed',
 'https://internal.canarabank.com/evidence/lcr-returns-setup-2024.pdf',
 'Daily LCR return submission configured in OSMOS. IT confirmed automation live.'),

-- MAP 3 (Board-approved LCR policy) → Treasury (dept 1), ESCALATED — past due
(3, 1, '2024-09-15 13:10:00', '2024-09-22 13:10:00', NULL,
 'escalated',
 NULL,
 'Board meeting scheduled for Oct 15 — policy approval delayed. SLA breached.'),

-- MAP 4 (KYC periodic updation) → KYC/AML (dept 2), completed
(4, 2, '2024-08-20 12:00:00', '2024-09-19 12:00:00', '2024-09-10 11:00:00',
 'completed',
 'https://internal.canarabank.com/evidence/kyc-risk-categorisation-policy-aug24.pdf',
 'Board-approved KYC risk categorisation policy updated. All branches notified via circular.'),

-- MAP 5 (STR filing in 7 days) → KYC/AML (dept 2), completed
(5, 2, '2024-08-20 12:05:00', '2024-09-19 12:05:00', '2024-09-05 14:00:00',
 'completed',
 'https://internal.canarabank.com/evidence/str-process-update-aug24.pdf',
 'STR filing workflow updated. Principal Officer trained. FIU portal access verified.'),

-- MAP 6 (V-CIP compliance certificate) → KYC/AML (dept 2), DISPUTED
(6, 2, '2024-08-20 14:30:00', '2024-09-19 14:30:00', NULL,
 'disputed',
 NULL,
 'KYC team disputes ownership — V-CIP infrastructure is IT, not KYC. Re-routing to IT & Cybersecurity.'),

-- MAP 6 also assigned to IT & Cybersecurity (dept 5) after dispute re-route
(6, 5, '2024-09-01 10:00:00', '2024-09-15 10:00:00', NULL,
 'escalated',
 NULL,
 'IT team owns V-CIP infrastructure setup. Compliance certificate pending. SLA breached.'),

-- MAP 7 (KFS for borrowers) → Retail Banking Compliance (dept 4)
(7, 4, '2024-10-01 14:00:00', '2024-10-22 14:00:00', NULL,
 'in_progress',
 NULL,
 'KFS template being drafted. Legal review in progress. Target: deploy on all digital lending portals.'),

-- MAP 8 (Nodal GRO appointment) → Retail Banking Compliance (dept 4)
(8, 4, '2024-10-01 14:05:00', '2024-10-22 14:05:00', NULL,
 'assigned',
 NULL,
 'HR to nominate senior manager. Pending board sub-committee approval.'),

-- MAP 9 (Quarterly CG report) → Legal & Regulatory Affairs (dept 7), SEBI SLA = 7 days, completed
(9, 7, '2024-10-10 17:00:00', '2024-10-17 17:00:00', '2024-10-16 15:00:00',
 'completed',
 'https://internal.canarabank.com/evidence/sebi-cg-q2fy25-filing.pdf',
 'Q2 FY25 corporate governance report filed with NSE and BSE on Oct 16. Within SLA.'),

-- MAP 10 (Whistleblower + Compliance Officer as KMP) — pending_review, no task yet
-- This MAP is in human review queue — no task assigned yet

-- MAP 11 (DIR-3 KYC filing by directors) → Legal (dept 7), MCA SLA = 7 days
(11, 7, '2024-09-01 12:00:00', '2024-09-08 12:00:00', NULL,
 'escalated',
 NULL,
 'Deadline was Sep 30. Several directors missed filing. DIN deactivation notices received. Legal escalating.'),

-- MAP 12 (Companies ensure directors file) → Legal (dept 7) + HR (dept 6)
(12, 7, '2024-09-01 12:05:00', '2024-09-08 12:05:00', NULL,
 'in_progress',
 NULL,
 'Legal sending reminder notices to all board directors.'),
(12, 6, '2024-09-01 12:10:00', '2024-09-08 12:10:00', NULL,
 'in_progress',
 NULL,
 'HR compiling list of directors who have not filed. Coordinating with Company Secretary.');



-- 6. SUB-TASKS


-- Task for MAP 1 (LCR run-off rate update) has 3 sub-tasks
INSERT INTO sub_tasks (task_id, description, status, completed_at, evidence_url) VALUES
(1, 'Update CBS ALM module run-off rate parameter from 5% to 7.5% for stable retail deposits.', 'completed', '2024-09-18 11:00:00', 'https://internal.canarabank.com/evidence/cbs-param-change-lcr.pdf'),
(1, 'Recompute LCR position with revised run-off rates and validate against 100% minimum threshold.', 'completed', '2024-09-19 14:00:00', 'https://internal.canarabank.com/evidence/lcr-recomputation-sep24.xlsx'),
(1, 'Submit revised LCR computation to CFO for sign-off before RBI reporting cycle.', 'pending', NULL, NULL);

-- Task for MAP 3 (Board-approved LCR policy) — 2 sub-tasks, one escalated
INSERT INTO sub_tasks (task_id, description, status, completed_at, evidence_url) VALUES
(3, 'Draft Board-approved LCR Policy document incorporating revised run-off rates and HQLA definition.', 'completed', '2024-09-25 10:00:00', 'https://internal.canarabank.com/evidence/lcr-policy-draft-v2.docx'),
(3, 'Present LCR Policy to Board of Directors for approval and obtain signed resolution.', 'escalated', NULL, NULL);

-- Task for MAP 6 (V-CIP compliance) — IT team sub-tasks
INSERT INTO sub_tasks (task_id, description, status, completed_at, evidence_url) VALUES
(7, 'Audit existing V-CIP infrastructure for compliance with RBI guidelines on liveness detection and face match.', 'completed', '2024-09-10 12:00:00', 'https://internal.canarabank.com/evidence/vcip-audit-report.pdf'),
(7, 'Remediate gaps found in V-CIP audit — upgrade liveness detection SDK to version 3.2.', 'pending', NULL, NULL),
(7, 'Obtain and submit V-CIP compliance certificate to RBI Regional Office within 90 days of circular.', 'escalated', NULL, NULL);

-- Task for MAP 7 (KFS for borrowers) — 3 sub-tasks
INSERT INTO sub_tasks (task_id, description, status, completed_at, evidence_url) VALUES
(8, 'Draft standardised Key Fact Statement (KFS) template containing APR, fees, charges, grievance officer details, and cooling-off period.', 'in_progress', NULL, NULL),
(8, 'Integrate KFS generation into digital lending origination system — auto-generate before loan execution.', 'pending', NULL, NULL),
(8, 'Train all digital lending relationship managers on KFS requirements and obtain acknowledgement.', 'pending', NULL, NULL);

-- Task for MAP 11 (DIR-3 KYC escalation) — 2 sub-tasks
INSERT INTO sub_tasks (task_id, description, status, completed_at, evidence_url) VALUES
(11, 'Identify all directors whose DIN has been deactivated due to non-filing of DIR-3 KYC.', 'completed', '2024-10-05 09:00:00', 'https://internal.canarabank.com/evidence/din-deactivation-list.xlsx'),
(11, 'File DIR-3 KYC for deactivated directors with Rs. 5000 fee and obtain DIN reactivation confirmation from MCA21.', 'in_progress', NULL, NULL);



-- 7. HUMAN REVIEW QUEUE
-- (MAPs with confidence < 0.85 flagged for review)


INSERT INTO human_review_queue (
    map_id, reason, created_at, resolved_at, resolution, resolved_by
) VALUES

-- MAP 6 (V-CIP) — low confidence, ambiguous ownership, now resolved
(
    6,
    'Confidence score 0.72. Ambiguous ownership between KYC/AML (policy) and IT & Cybersecurity (infrastructure). V-CIP spans both departments.',
    '2024-08-20 11:15:00',
    '2024-08-20 14:00:00',
    'modified',
    'rajesh.kumar@canarabank.com'
),

-- MAP 10 (Whistleblower + KMP) — low confidence, pending review
(
    10,
    'Confidence score 0.74. MAP spans HR & Conduct (whistleblower policy implementation) and Legal & Regulatory Affairs (LODR filing and KMP designation). Requires human decision on primary owner.',
    '2024-10-10 16:10:00',
    NULL,
    NULL,
    NULL
),

-- MAP 11 (DIR-3 KYC) — medium confidence but escalated due to deadline proximity
(
    11,
    'Confidence score 0.93 but flagged due to deadline risk: compliance date is September 30 and circular ingested September 1 — only 29 days. Escalated for priority assignment.',
    '2024-09-01 11:05:00',
    '2024-09-01 12:00:00',
    'approved',
    'priya.nair@canarabank.com'
);



-- 8. AUDIT LOG
-- Full trail of all agent actions across the pipeline


INSERT INTO audit_log (entity_type, entity_id, action, actor, timestamp, payload) VALUES

-- Circular 1 lifecycle
('circular', 1, 'circular_ingested', 'watcher_agent', '2024-09-15 11:45:00',
 '{"source": "RBI", "url": "https://rbi.org.in/Scripts/NotificationUser.aspx?Id=12601", "dedup_hash": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"}'),

('circular', 1, 'status_changed', 'map_extractor', '2024-09-15 12:00:00',
 '{"before": {"status": "pending"}, "after": {"status": "processing"}}'),

('circular', 1, 'status_changed', 'map_extractor', '2024-09-15 12:15:00',
 '{"before": {"status": "processing"}, "after": {"status": "processed"}, "maps_extracted": 3}'),

-- MAP 1 lifecycle
('map', 1, 'map_extracted', 'map_extractor', '2024-09-15 12:00:00',
 '{"confidence_score": 0.97, "circular_id": 1, "auto_approved": true, "model": "gpt-4o-mini"}'),

('map', 1, 'status_changed', 'router_agent', '2024-09-15 13:00:00',
 '{"before": {"status": "approved"}, "after": {"status": "assigned"}, "routed_to": "Treasury & Investments", "rag_confidence": 0.94}'),

-- MAP 2 completed
('map', 2, 'map_extracted', 'map_extractor', '2024-09-15 12:05:00',
 '{"confidence_score": 0.94, "circular_id": 1, "auto_approved": true, "model": "gpt-4o-mini"}'),

('map', 2, 'status_changed', 'router_agent', '2024-09-15 13:05:00',
 '{"before": {"status": "approved"}, "after": {"status": "assigned"}, "routed_to": "Treasury & Investments"}'),

('map', 2, 'status_changed', 'validator_agent', '2024-09-20 10:00:00',
 '{"before": {"status": "in_progress"}, "after": {"status": "completed"}, "evidence_verified": true}'),

-- MAP 3 escalated
('map', 3, 'status_changed', 'notifier_agent', '2024-09-23 09:00:00',
 '{"before": {"status": "in_progress"}, "after": {"status": "escalated"}, "reason": "SLA_breached", "due_at": "2024-09-22T13:10:00", "notified": ["treasury.compliance@canarabank.com", "audit.chief@canarabank.com"]}'),

-- MAP 6 dispute and re-route
('map', 6, 'flagged_for_review', 'map_extractor', '2024-08-20 11:10:00',
 '{"confidence_score": 0.72, "reason": "Ambiguous ownership KYC vs IT", "circular_id": 2}'),

('map', 6, 'status_changed', 'human:rajesh.kumar@canarabank.com', '2024-08-20 14:00:00',
 '{"before": {"status": "pending_review"}, "after": {"status": "approved"}, "resolution": "modified", "note": "Primary owner IT for infrastructure; KYC for policy. Split task created."}'),

('map', 6, 'status_changed', 'router_agent', '2024-08-20 14:30:00',
 '{"before": {"status": "approved"}, "after": {"status": "assigned"}, "routed_to": ["KYC / AML", "IT & Cybersecurity"], "split_task": true}'),

('task', 6, 'status_changed', 'validator_agent', '2024-09-19 10:00:00',
 '{"before": {"status": "assigned"}, "after": {"status": "disputed"}, "reason": "KYC team disputes infrastructure ownership", "department": "KYC / AML"}'),

-- MAP 9 completed (SEBI LODR)
('map', 9, 'map_extracted', 'map_extractor', '2024-10-10 16:00:00',
 '{"confidence_score": 0.96, "circular_id": 4, "auto_approved": true, "model": "gpt-4o-mini"}'),

('map', 9, 'status_changed', 'router_agent', '2024-10-10 17:00:00',
 '{"before": {"status": "approved"}, "after": {"status": "assigned"}, "routed_to": "Legal & Regulatory Affairs", "rag_confidence": 0.91}'),

('map', 9, 'status_changed', 'validator_agent', '2024-10-16 15:00:00',
 '{"before": {"status": "in_progress"}, "after": {"status": "completed"}, "evidence_verified": true, "evidence_url": "https://internal.canarabank.com/evidence/sebi-cg-q2fy25-filing.pdf"}'),

-- Notifications
('notification', 1, 'notification_sent', 'notifier_agent', '2024-09-15 13:00:00',
 '{"type": "assignment", "channel": "email", "recipient": "treasury.compliance@canarabank.com", "map_id": 1, "due_at": "2024-09-22"}'),

('notification', 2, 'notification_sent', 'notifier_agent', '2024-09-23 09:00:00',
 '{"type": "escalation", "channel": "slack", "recipient": "#treasury-compliance", "map_id": 3, "reason": "SLA_breached", "escalated_to": "audit.chief@canarabank.com"}');



-- 9. NOTIFICATIONS LOG


INSERT INTO notifications_log (
    task_id, department_id, channel, notification_type, sent_at, status
) VALUES

-- Assignment notifications
(1,  1, 'email', 'assignment',  '2024-09-15 13:00:00', 'sent'),
(2,  1, 'email', 'assignment',  '2024-09-15 13:05:00', 'sent'),
(3,  1, 'email', 'assignment',  '2024-09-15 13:10:00', 'sent'),
(4,  2, 'email', 'assignment',  '2024-08-20 12:00:00', 'sent'),
(5,  2, 'email', 'assignment',  '2024-08-20 12:05:00', 'sent'),
(6,  2, 'email', 'assignment',  '2024-08-20 14:30:00', 'sent'),
(8,  4, 'email', 'assignment',  '2024-10-01 14:05:00', 'sent'),
(11, 7, 'email', 'assignment',  '2024-09-01 12:00:00', 'sent'),

-- Reminders (SLA approaching)
(1,  1, 'slack', 'reminder',    '2024-09-20 09:00:00', 'sent'),
(3,  1, 'slack', 'reminder',    '2024-09-21 09:00:00', 'sent'),
(7,  5, 'slack', 'reminder',    '2024-09-12 09:00:00', 'sent'),

-- SLA breach escalations
(3,  1, 'slack',  'escalation', '2024-09-23 09:00:00', 'sent'),
(3,  9, 'email',  'escalation', '2024-09-23 09:01:00', 'sent'),
(7,  5, 'email',  'escalation', '2024-09-16 09:00:00', 'sent'),
(7,  9, 'slack',  'escalation', '2024-09-16 09:01:00', 'sent'),
(11, 7, 'email',  'breach',     '2024-09-09 09:00:00', 'sent'),
(11, 9, 'slack',  'breach',     '2024-09-09 09:01:00', 'sent'),

-- Failed notification (Slack webhook down)
(12, 6, 'slack',  'assignment', '2024-09-01 12:10:00', 'failed');