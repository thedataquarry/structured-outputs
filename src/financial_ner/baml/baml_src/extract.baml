class Entities {
  Company string[]? @description(#"
    Official or unofficial name of a registered company or a brand.
  "#)
  Date string[]? @description(#"
    Specific time period, whether explicitly mentioned (e.g., "year ended March 2020") or implicitly referred to (e.g., "last month"), in the past, present, or future.
  "#)
  Location string[]? @description(#"
    Represents geographical locations, such as political regions, countries, states, cities, roads, or any other location, even when used as adjectives.
  "#)
  Money string[]? @description(#"
    Monetary value expressed in any world currency, including digital currencies.
  "#)
  Person string[]? @description(#"
    Name of an individual.
  "#)
  Product string[]? @description(#"
    Any physical object or service manufactured or provided by a company to consumers, excluding references to businesses or sectors within the financial context.
  "#)
  Quantity string[]? @description(#"
    Any numeric value that is not categorized as Money, such as percentages, numbers, measurements (e.g., weight, length), or other similar quantities. Note that unit of measurements are also part of the entity.
  "#)
}

function ExtractEntities(text: string) -> Entities {
  client OpenRouterGoogleGemini3Flash
  prompt #"
    Identify and extract entities from the following financial news text into the following categories:
    For each category:
    - Extract all relevant entities as a list of strings, preserving the wording from the text
    - Use None if no entities are found in that category
    - Only extract entities that are explicitly mentioned in the text itself, do not make inferences or reason about what entities might be implied based on URLs, domain names, or other indirect references
    - Extract individual items rather than compound or ranged entities (e.g., if a range or compound entity is mentioned, extract each individual item separately)

    {{ ctx.output_format }}

    {{ _.role("user") }}
    {{ text }}
  "#
}

test test_1 {
  functions [ExtractEntities]
  args {
    text #"
    On November 30 , 2012 , the Company entered into a credit facility with Wells Fargo as Administrative Agent and PennantPark as Lenders , replacing the Company s Credit Agreement , dated as of June 15 , 2010 , as amended , with Bank of America , N.A. as Administrative Agent and Keybank National Association as Lender .
    "#
  }
  @@assert(a1, {{ this.Company and "Bank of America , N.A." in this.Company }})
  @@assert(a2, {{ this.Company and "Keybank National Association" in this.Company }})
  @@assert(a3, {{ this.Company and "PennantPark" in this.Company }})
  @@assert(a4, {{ this.Company and "Wells Fargo" in this.Company }})
  @@assert(a5, {{ this.Date and "June 15 , 2010" in this.Date }})
  @@assert(a6, {{ this.Date and "November 30 , 2012" in this.Date }})
}
