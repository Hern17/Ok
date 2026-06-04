#set text(font: "Libertinus Serif", size: 11pt)
#show heading: set text(font: "Libertinus Serif")
#show link: underline
#set page(margin: (x: 0.9cm, y: 1.3cm))
#set par(justify: true)

#let chiline() = { v(-3pt); line(length: 100%); v(-5pt) }
#let lastupdated(date) = { h(1fr); text("Last Updated in " + date, fill: gray) }

= Test User
test@example.com  |  +6012-345-6789  |  KL, Malaysia \
https://linkedin.com/in/test \
https://github.com/test \

== Education Background
#chiline()

*UM* — CS #h(1fr) 2021-2025 \
*Stage*: bachelor \
*Results / GPA*: 3.8 \
*Subjects (max 4, comma separated)*: Algorithms, Data Structures \
- Debate Club
*Location*: KL \

== Work Experience
#chiline()

*Google* — SWE Intern #h(1fr) 2024 \
- Built APIs and learned Go
*Skills Obtained*: Python, Docker, Go \
*Location*: KL \

== Leadership & Extra-Curricular
#chiline()

*Debate Club* — President #h(1fr) 2023-2024 \
- Led team of 20 members
*Location*: UM \

== Projects
#chiline()

*Chatbot* #h(1fr) 2023 \
*Project Type*: personal \
- Built NLP pipeline with 95% accuracy
*Link / ID / Proof*: github.com/test/chatbot \

== Certifications
#chiline()

- 2_hi_CV.pdf

== Skills
#chiline()

*Python*, *Docker*

#lastupdated("Jun 04, 2026")