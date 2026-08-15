# Interview — Accounts Payable Manager (purchasing / invoice-to-pay)

Date: 2026-06-02
Present: AP Manager (Marisol Vance), engagement lead
Scope discussed: invoice receipt through vendor statement reconciliation

## Invoice receipt

"Basically everything comes to ap-invoices@. Vendors are told to send it
there on the PO terms, and I'd say nine out of ten do. The clerk works the
mailbox first thing — he drags the PDFs into Ephesoft, and Ephesoft reads
the header and drops a pending bill into NetSuite. When it can't find the PO
number on the face of the invoice it dumps the thing into a validation queue
and somebody keys it by hand."

"NetSuite won't let the same supplier and invoice number in twice, so at
least we're not double-paying. That one I trust."

"The confidence threshold on the OCR — I want to say seventy-five percent?
Nobody has pulled the configuration since the implementation partner left."

## Matching

"For PO invoices it's the three-way match: my bill, the PO line, the item
receipt from the dock. Inside tolerance it releases itself. Outside, it
holds and it becomes my problem."

"I need the receipt to judge a quantity variance and so does whoever is
working the hold queue — we're both looking at the same item receipt in
NetSuite, just at different moments."

"Half the holds are not real variances. They're receipts the dock posted
late. It eats my Fridays. I sit there re-running the match on things that
were always going to clear once receiving caught up." (Asked whether this
was a documentation problem: no — she was clear the process is understood,
it is the timing that hurts.)

## Exceptions

"The hold queue has no system control on it, honestly. It's me and my senior
deciding. There's no approval step in NetSuite for a variance disposition —
you just change it and move on. I log the reason code because I want the
history, not because anything makes me."

## Payment

"Once it's released it lands in the Friday run. I export the payment
proposal to Excel, the Controller reviews it, and then treasury uploads and
releases in Chase Connect — two different logins for upload and release,
that one is real."

## Statements

"Statements I do monthly for the big vendors. I tick off what we've paid
against what they show and chase the difference. The worksheet goes on the
shared drive. Nobody downstream uses it — it's for me, and for you people
when you ask."
