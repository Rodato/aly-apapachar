**Aly Flagging, Escalation, and Response Protocol**

The purpose of this document is to outline a practical safety and escalation framework for Aly. It is designed to help us do three things consistently:

1. Classify risk in user or facilitation inputs using a shared flagging system  
2. Define the operational response when a message is flagged, especially in medium and higher risk cases.  
3. Provide example messages that can be used to train Aly and guide human follow-up.

This protocol is intended to help Aly distinguish between different types of concerns and ensure that the response is accurate, timely, and documented. Aly may receive inputs from users that may be problematic. These inputs tend to fall into two broad categories:

- Normative harm: statements that reinforce harmful beliefs, coercive norms, sexism, or control.  
- Safety harm: statements that suggest a person may endanger someone else or themselves, or that violence, coercion, abuse, or severe harm may already be occurring.

Aly should be able to distinguish these two different types of categories and implement a set of responses and flagging systems that help the managing team monitor and respond to risky usage.

**Guiding Principles**

1. **Safety first**: When a message indicates possible danger to a person, Aly should prioritize flagging the interaction and escalate over educational dialogue alone.  
2. **Human oversight matters**: Aly can classify, prompt, and support, but it should not be the final decision-maker in high-risk cases. High-risk alerts should route to a human who can assess context or an organization that can support the user.  
3. **Not every problematic statement requires the same response:** Some situations call for a lightweight corrective response; others require urgent escalation.  
4. **Responses should be short, direct, supportive, and action-oriented.** Messages that are too long are less likely to be read or used effectively.  
5. **Documentation and traceability**: Every flagged case should generate a clear record of what happened, how it was classified, who was notified, and what action was taken.  
6. **Alignment with local reporting requirements**: Where required, this protocol must be aligned with country-specific reporting obligations, partner requirements, and legal guidance. The bot should not make legal determinations on its own; it should route such cases for human review.

**When should the protocol be activated?**  
When Aly receives content that is:

- sexist, degrading, or harmful jokes  
- normalization of coercion or control  
- admissions of violence or threats of violence  
- sexual coercion or non-consensual sexual conduct  
- stalking, harassment, or intimidation  
- economic or social control  
- statements suggesting imminent harm

1. **Flagging System Classification**

The flagging system should classify inputs into three levels: Low, Medium, and High.

**LOW FLAG RISK** 

| Definition: Low-risk flags refer to inputs that reinforce harmful beliefs or stereotypes (normative harm) but do not indicate immediate danger, direct threats, or explicit disclosures of violence (safety harm). Low-risk content still matters because it shapes norms, lowers the threshold for more serious harm, and can make a space feel unsafe. However, it does not usually require emergency escalation |  |  |
| :---- | :---- | :---- |
| Typical characteristics | Aly’s responses | Examples of input  |
| sexist jokes or demeaning humor memes shared, comments made, or anecdotes that normalize inequality dismissive or mocking comments about consent, gender, or power language that reflects harmful beliefs without a direct statement of abuse or intent | Aly’s responses should: interrupt the harmful norm reinforce group expectations or safer behavior offer a brief corrective response log the incident for pattern tracking Example of response: “That comment may seem casual, but it can reinforce harmful ideas. Please redirect the conversation toward respect and constructive participation.” “That comment may seem casual, but it can cause pain and discomfort for some. Here are some strategies to address the big elephant in the room.” | “It was just a joke, women are too sensitive.” “That’s just how men are.” “She should know how to take a joke.” “If she gets offended, that’s her problem.”  |

**MEDIUM FLAG RISK**

| Definition: Medium-risk flags refer to inputs that suggest intentional reinforcement of coercive or harmful norms, recurring disruptive behavior, or forms of control and abuse that are serious but not clearly imminent. Medium-risk cases often signal behavior patterns that can escalate. These cases may require a direct check-in, manager awareness, and a documented follow-up rather than only a corrective message. |  |  |
| :---- | :---- | :---- |
| Typical characteristics | Aly’s responses should… | Examples |
| repeated sexist or violent commentary explicit endorsement of controlling behavior minimizing abusive conduct repeated trolling or intentional disruption around gender, violence, or safety topics indications of harassment, stalking, social control, or economic control without immediate danger cues | identify the pattern interrupt and name the concern prompt human follow-up within a defined time window record the case and next action | “I check her phone because that’s what responsible partners do.” “She shouldn’t be going out with male friends if she respects me.” “I control the money because otherwise she wastes it.” “I keep calling until she answers so she knows I’m serious.”  |

**HIGH FLAG RISK**

| Definition: High-risk flags refer to content indicating violence, threat, coercion, severe abuse, sexual violence, imminent danger, or conduct that may require urgent intervention, referral, or mandatory reporting review. These cases may require rapid human intervention. Aly should NOT attempt to resolve them through messages. |  |  |
| :---- | :---- | :---- |
| Typical characteristics | Aly’s responses should… | Examples |
| admissions of physical violence threats to hurt a partner, family member, or someone else statements suggesting imminent loss of control sexual coercion or sex without consent stalking accompanied by threats, obsession, or escalation explicit statements of intent to retaliate, force contact, or “make” someone comply signs that a participant or another person may be in immediate danger | trigger urgent flag in the dashboard provide immediate referral or support language route for operational and, where applicable, legal review | “She didn’t want to have sex, but I made her anyway.” “If she leaves me, I don’t know what I’ll do.” “I slapped her to remind her who’s in charge.” “When I’m angry, I’m afraid I might hurt her.” “I’ll keep showing up until she takes me back.”  |

**Harm Taxonomy Aly Should Recognize**  
To classify effectively, ALI should be trained to recognize not only physical violence but a wider set of harms, including:

Physical violence: Hitting, slapping, pushing, grabbing, choking, throwing objects, or using force.

Psychological or emotional abuse: Insults, humiliation, intimidation, threats, belittling, fear-based control, or emotional manipulation.

Sexual violence or coercion: Non-consensual sex, pressure for sex, coercive insistence, sexual entitlement, or inability to recognize consent.

Social control: Restricting movement, friendships, communication, work, learning, or family contact.

Economic control: Restricting money, monitoring expenses excessively, forcing financial dependence, or coercing financial actions.

Harassment and stalking: Repeated unwanted messages or calls, digital surveillance, monitoring social media, following someone, or refusing to stop contact.

Threats and intimidation: Statements that imply punishment, retaliation, loss of control, or future violence.

Self-harm or harm-to-others signals: Statements that suggest imminent emotional crisis, loss of control, or potential violence toward self or others.

**2\. Operational Map**

This section describes what should happen once ALI flags a message.

1. **Core operational roles**

The following roles should exist in the workflow, even if one person covers multiple functions in practice:

* **Aly**: classifies the message and triggers the workflow in the dashboard.  
* **Facilitator or bot user**: the person interacting in the field or session with Aly.  
* **Field supervisor**: the first operational reviewer for flagged cases.  
* **Safety lead / designated escalation owner**: reviews the most serious cases and advises on action.  
* **Dashboard owner**: ensures cases are logged, tracked, and auditable.  
* **Legal / compliance partner** (when needed): advises on reporting requirements or mandatory escalation.  
* **Referral network / human support resource**: the person or service or organization that can provide direct follow-up or specialized support.

2. **Operational flow by flag level**

A. Low flag workflow

1. Aly detects low-risk content.  
2. Aly provides a brief corrective or redirective response.  
3. The event is logged automatically.  
4. No immediate alert is required.  
5. If a repeated pattern emerges, the case is reclassified to medium.

B. Medium flag workflow

1. Aly detects medium-risk content.  
2. Aly provides a brief response that names the concern and discourages the behavior.  
3. A notification / medium flag is sent to the dashboard.  
4. The case is logged with message content, classification, time, and participant/session identifier.  
5. A human follow-up occurs within the dashboard for review.  
6. If the follow-up reveals escalation, repeat behavior, or further concerning context, the case is upgraded to high.

**Suggested service standard:** human follow-up within the same day, ideally within a few hours.

C. High flag workflow

1. Aly detects high-risk content.  
2. Aly provides a short supportive and safety-oriented response; it should not attempt to solve the case on its own.  
3. An immediate alert is sent to the field manager and the designated safety lead.  
4. The incident is logged in the dashboard.  
5. A human reviews the case as quickly as possible.  
6. The human determines whether outreach, referral, reporting review, or additional escalation is needed.  
7. The outcome and rationale are documented.  
8. If required by law, partner agreement, or safeguarding policy, the case is reviewed for formal reporting.

**Suggested service standard:** urgent review as soon as operationally possible; highest-priority cases should be treated as near-real-time where feasible.

**Escalation rules**

A case should automatically escalate upward when any of the following is true:

* there is mention of current or recent violence  
* there is mention of sexual coercion or lack of consent  
* there is a threat of future harm  
* there is evidence of stalking or coercive pursuit after a breakup  
* a participant appears unable to control violent impulses  
* a medium-risk behavior repeats multiple times  
* a facilitator or reviewer feels uncertain and wants human review

When in doubt, the protocol should favor escalation

**Response time-logic**

There should be a direct relationship between severity and response speed:

* **Low**: corrective response and log  
* **Medium**: corrective response, alert, and same-day follow-up  
* **High**: immediate alert, urgent human review, and referral/reporting assessment

At the beginning of deployment, the team may choose to add human follow-up to nearly all flagged cases in order to build trust and learn from the system

**Recommended Response Design**

messages should follow a consistent structure:

1. **Acknowledge** what was shared.  
2. **Name the concern** clearly and simply.  
3. **Set a boundary or expectation** when needed.  
4. **Encourage safer action** or de-escalation.  
5. **Route to a human or referral** when appropriate.

Responses should avoid:

* long lectures  
* overly clinical wording  
* legal conclusions stated as fact unless reviewed  
* moralizing language that shuts down disclosure  
* false reassurance in high-risk cases

**Exemplary Messages for Training and Response for Aly**

The examples below can be used for both classifier training and response drafting. They should be refined over time with local language and real usage patterns.

**8.1 Low-risk examples**

Example 1: sexist joke

Input: “Someone made a joke about women being too emotional and everyone laughed.”

Classification: Low

ALI response: “Comments like that can reinforce harmful ideas, even when they’re framed as jokes. A better next step is to redirect the conversation and reinforce respectful norms in the group.”

Example 2: minimizing sexist content

Input: “It was just a meme. People are overreacting.”

Classification: Low

Aly response: “Even when something seems minor, it can still make the space feel unsafe or normalize disrespect. It’s worth addressing briefly and clearly.”

**8.2 Medium-risk examples**

Example 3: social control

Input: “I don’t let my partner go out with certain friends because I know how that ends.”

Classification: Medium

Aly response: “Restricting who a partner sees can be a form of control. This should be flagged for follow-up, with a response that reinforces respect, autonomy, and healthy boundaries.”

Example 4: economic control

Input: “She doesn’t need access to the money. I handle all of that.”

Classification: Medium

Aly response: “Controlling a partner’s access to money can be a serious warning sign. This should be documented and reviewed, with a short response that names the concern and routes for human follow-up.”

Example 5: repeated hostile disruption

Input: “I keep telling the group that women exaggerate abuse and I’m not going to stop.”

Classification: Medium

Aly response: “This is repeated harmful disruption and should not be treated as a one-off comment. It should be flagged, logged, and escalated for direct follow-up.”

**8.3 High-risk examples**

Example 6: physical violence

Input: “I pushed her during an argument, but it wasn’t a big deal.”

Classification: High

Aly’s response: “What you’ve described is physical violence. This needs urgent human follow-up. A person from the team should review this case and determine the safest next step.”

Example 7: sexual coercion

Input: “She didn’t want to have sex, but I insisted until she gave in.”

Classification: High

Aly response: “This raises a serious concern about consent and sexual coercion. This should be escalated immediately for human review and appropriate support or reporting assessment.”

Example 8: fear of harming partner

Input: “I’m scared that if I get that angry again, I might hurt her.”

Classification: High

Aly response: “This suggests a risk of imminent harm and should be treated urgently. The priority is immediate human follow-up and connection to support.”

Example 9: stalking after separation

Input: “I’ll keep showing up until she talks to me. I’m not giving up.”

Classification: High

Aly response: “This may indicate stalking or coercive pursuit after a breakup. It should be escalated immediately and not handled as a routine relationship issue.”

**Message bank for operational use**

Below are short-form message templates that can be adapted for Aly.

Low flag message

“Thanks for sharing this. That kind of comment can reinforce harmful ideas, even if it was meant casually. I’d suggest redirecting the conversation and reinforcing respectful group norms.”

Medium flag message

“Thanks for flagging this. What was described may reflect controlling or harmful behavior. I recommend documenting it and following up directly, since it may require more than a simple in-the-moment response.”

High flag message

“Thanks for sharing this. What’s described here raises a serious safety concern. This should be escalated to a human right away so the appropriate next step can be taken.”

**Implementation guidance**

For classifier training

The model should be trained on in the Apapachar sprint:

* short realistic examples  
* localized phrasing and slang  
* borderline cases between low and medium  
* borderline cases between medium and high  
* examples where harmful behavior is minimized, joked about, or disguised as care  
* examples involving consent, jealousy, control, and escalation after separation

For benchmarking

A benchmark set should test whether Aly can:

* correctly classify low, medium, and high-risk cases  
* distinguish harmful norms from immediate safety risks  
* recognize non-physical forms of abuse such as economic or social control  
* identify when to escalate to human review  
* generate short, usable, non-verbose responses

For operations

Before scaling, the team should confirm:

* who receives each alert type  
* expected response times  
* where records are stored  
* who owns case review  
* what referral resources are available locally  
* what legal or partner reporting requirements apply

**In conclusion, Aly should not only respond helpfully; it should respond responsibly. A strong protocol makes it possible to classify risk consistently, route serious concerns, and build trust in the system over time. The goal is not to overreact to every problematic statement, but to make sure harmful norms are addressed, serious risks are escalated, and no one is left alone with a critical safety issue.**  
