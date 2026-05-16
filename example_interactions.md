# Example Interaction Log

These interactions were captured against the four PDFs currently in `data/`:

- `20220719.pdf`
- `20221122.pdf`
- `20230807.pdf`
- `20231208.pdf`

## 1. Ukraine / Bucha lookup

Question:

`Which document mentions Bucha, Ukraine and the Stanislavchuk family?`

Server answer:

```json
{
  "answer": "CLAES OLDENBURG, 1929-2022 BUCHA, Ukraine — For the first time since the war began, the Stanislavchuk family was togeth- er again.",
  "citations": [
    {
      "document_name": "20220719.pdf",
      "page_number": 1,
      "snippet": "CLAES OLDENBURG, 1929-2022 BUCHA, Ukraine — For the first time since the war began, the Stanislavchuk family was togeth- er again."
    }
  ]
}
```

## 2. Child welfare / ACS lookup

Question:

`Which document talks about New York City Administration for Children's Services bias against Black families?`

Server answer:

```json
{
  "answer": "worker in For decades, Black families have complained that New York City’s welfare agency , the Admin- istration for Children’s Services, is biased against them. worker in For decades, Black families have complained that New York City’s welfare agency , the Admin- istration for Children’s",
  "citations": [
    {
      "document_name": "20221122.pdf",
      "page_number": 1,
      "snippet": "worker in For decades, Black families have complained that New York City’s welfare agency , the Admin- istration for Children’s Services, is biased against them."
    }
  ]
}
```

## 3. Multi-document query

Question:

`Which document mentions Gaza and which document mentions congestion pricing?`

Server answer:

```json
{
  "answer": "At the sites of attacks in Israel and battles in Gaza, the military has found items that detail the lo- cation of Hamas installations and tunnels, including how the armed group operates underground, ac- cording to documents and other information made available by the Israeli military for The New York Times to review. And this lat- est battle has given rise to a curi- ous new set of allies and enemies, allegations of hypocrisy and vivid trash talk — a situation that may grow only more intense as the start of congestion pricing nears, possibly in May next year . T rash T alk Across the Hudson In a Congestion Pricing Fight By TRACEY TULL Y Continued on Page A19 Pro-Climate Governor Supports Drivers LEGACY Megan Rapinoe leaves a mark beyond the field.",
  "citations": [
    {
      "document_name": "20231208.pdf",
      "page_number": 1,
      "snippet": "At the sites of attacks in Israel and battles in Gaza, the military has found items that detail the lo- cation of Hamas installations and tunnels, including how the armed group operates underground, ac- cording to docume"
    },
    {
      "document_name": "20230807.pdf",
      "page_number": 1,
      "snippet": "And this lat- est battle has given rise to a curi- ous new set of allies and enemies, allegations of hypocrisy and vivid trash talk — a situation that may grow only more intense as the start of congestion pricing nears, "
    }
  ]
}
```
