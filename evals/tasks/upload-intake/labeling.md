# Labeling rules (Snapnote image uploads)

1. `document`: a page or part of a page of printed or written text: forms, letters, receipts, reports, tables printed on paper.
2. `screenshot`: a capture of a phone or computer screen, such as an app or website.
3. `chart`: a bar, line or pie chart or another plot of data, as an image on its own.
4. `book_cover`: the front cover of a book.
5. `photo`: a camera photo of the world: people, places, objects, food, packaging, even when it contains text.
6. `diagram`: a drawn illustration or schematic: science diagrams, icons, puzzles, clip art, educational pictures.
7. A photo of a document or a screen taken with a phone camera is `document` or `screenshot` only if the page or screen fills most of the frame; otherwise it is `photo`.
8. `readable_text` asks whether a person could read at least one word. Text too small or blurry to read is `false`.
9. `usable` is about whether a person can tell what the image shows at all. A plain but sharp image is `true`. Every kind can be unusable.
