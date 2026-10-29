# Labeling rules (Fastbite support)

1. `late_order`: the order has not arrived yet or arrived late, and that is the main complaint or question.
2. `missing_or_wrong_item`: something ordered is missing, or a different item came.
3. `food_quality`: the food arrived but is cold, spilled, spoiled, undercooked or tastes wrong.
4. `payment_refund`: charges, double charges, refunds already promised, payment methods, vouchers that failed at checkout.
5. `account_access`: login, verification codes, a locked or hacked account, changing phone number or email. Deleting an account is `human_review`.
6. `human_review`: everything else, including restaurant or rider feedback without a problem to fix, partnership or job enquiries, messages with no clear request, and messages that clearly raise **two or more** of the queue problems above ("my order was late AND a drink was missing").
7. A safety report always keeps its queue by the rules above **and** sets `safety: true`. A safety report with no other problem (e.g. "the rider was driving dangerously") goes to `human_review`.
8. Asking for a refund because of a food problem is still the food problem's queue (`food_quality` or `missing_or_wrong_item`), with `compensation: true`. `payment_refund` is for problems with the money itself.
9. "Where is my refund?" for a refund already promised is `payment_refund`.
10. Sarcasm and anger do not change the queue.
11. `safety` covers reported harm or a concrete hazard: allergic reactions, symptoms after eating, foreign objects (hair, plastic, metal), raw or spoiled food, and dangerous rider behaviour. Food that is only cold, spilled or late is not a safety problem.
12. `compensation` is `true` only when the customer asks for money back, credit or a voucher, or chases a refund already promised. Reporting an overcharge without asking for anything is `false`.
