enum Channel {
  Email
  Phone
  Portal
  In_Person
}

enum CoverageType {
  Property
  Auto
  Liability
  Health
  Travel
  Other
}

enum ObjectType {
  Vehicle
  Building
  Person
  Other
}

enum IncidentType {
  Rear_End_Collision
  Side_Impact_Collision
  Head_On_Collision
  Parking_Lot_Collision
  House_Fire
  Kitchen_Fire
  Electrical_Fire
  Burst_Pipe_Flood
  Storm_Damage
  Roof_Leak
  Slip_and_Fall
  Property_Injury
  Product_Liability
  Theft_Burglary
  Vandalism
}

enum LocationType {
  Intersection
  Highway
  Parking_Lot
  Driveway
  Residential_Street
  Residence_Interior
  Residence_Exterior
  Commercial_Property
  Public_Property
}


class ClaimHeader {
  claim_id string? @description("Claim ID in format CLM-XXXXXX, where X is a digit")
  report_date string? @description("Date of the report in YYYY-MM-DD format")
  incident_date string? @description("Date incident occurred in YYYY-MM-DD format")
  reported_by string? @description("Full name of person reporting the claim")
  channel Channel? @description("Channel used to report the claim")
}


class PolicyDetails {
  policy_number string? @description("Policy number in format POL-XXXXXXXXX, where X is a digit")
  policyholder_name string? @description("Full legal name on policy")
  coverage_type CoverageType? @description("Type of insurance coverage")
  effective_date string? @description("Policy effective start date in YYYY-MM-DD format")
  expiration_date string? @description("Policy expiration end date in YYYY-MM-DD format")
}

class InsuredObject {
  object_id string? @description("For vehicles, use VIN format (e.g., VIN12345678901234567). For buildings, use PROP-XXXXXX format. For liability, use LIAB-XXXXXX format. For other objects, use OBJ-XXXXXX format, where X is a digit")
  object_type ObjectType? @description("Type of insured object")
  make_model string? @description("Make and model for vehicles (use standardtized manufacturer names and models), or building type for property ")
  year int? @description("Year model for vehicles or year built for buildings")
  location_address string? @description("Full street address where object is located or originated from")
  estimated_value int? @description("Estimated monetary value in USD without currency symbol")
}

class IncidentDescription {
  incident_type IncidentType? @description("Specific standartized incident type")
  location_type LocationType? @description("Standatdized location type where incident occurred")
  estimated_damage_amount int? @description("Estimated damage amount in USD without currency symbol")
  police_report_number string? @description("Police report number")
}

class InsuranceClaim {
  header ClaimHeader | null
  policy PolicyDetails | null
  insured_objects InsuredObject[] | null
  incident_description IncidentDescription | null
}

// Create a function to extract the resume from a stringing.
function ExtractInsuranceClaim(text: string) -> InsuranceClaim {
  client OpenRouterGoogleGemini3Flash
  prompt #"
    Extract the insurance claim information from the following text.
    - If you are unsure about a field, leave it as null.

    {{ ctx.output_format }}

    {{ _.role("user") }}
    {{ text }}
  "#
}



// Test the function with a sample resume. Open the VSCode playground to run this.
test test_1 {
  functions [ExtractInsuranceClaim]
  args {
    text #"
    Email received: 2024-04-22]\n\nSubject: Property claim from Jennifer Garcia—CLM-424063 (Shopping Center Incident)\n\nHi—this is Jennifer Garcia, and I'm writing because, honestly, I'm still kind of in shock about what happened this morning. They gave me this claim reference CLM-424063 when I called the help line earlier, but I figured I should also email so everything's in writing—it's just been a really stressful day, and I want to make sure nothing gets missed. Not sure how these things usually work, I guess you'll get back to me? Anyway...\n\nI'm the owner on Policy POL-787532354, with property coverage for my home at 6650 Broadway in Georgetown (you probably have it already under the id 656048, it's the single-family one built in ‘72—big front yard, needs new gutters, but that's not the issue today). My policy's only been active since December 20th of last year, I think it's valid through all of June. My daughter had a doctor's appointment at the clinic near the shopping center, so I parked in the lot there at around 8:30 AM and ran inside. When we came back, there were these broken flowerpots and spray paint all over part of our fence panels—they'd actually hauled stuff from some landscaping shop or something and smashed it on our property. I don't even know who'd do that. It looked intentional, not like an accident, and my neighbor Sandra saw two teenagers running off but couldn't see any faces.\n\nI called the police right away and got the report number (PR-20250822-4864, if that helps). The officer said it counted as property damage, and they made a note of everything. So here's everything, I hope.\n\nNothing's really happened like this before, so I'm not sure what to expect, but honestly it looks like around $5,800 worth of repairs—$5,834 is what the contractor estimated, anyway, though my husband keeps thinking it'll cost more with labor. The main thing is the cosmetic repairs, but now I'm worried about the wood swelling if it rains this week. It's just so frustrating because we only painted that fence last year! Oh, and I hope this email is okay for the claim—I never know if I should call again. I did get an email confirmation back when I called in too.\n\nLet me know if you need more info or pictures (I've got like 40 on my phone, some are blurry because my dog was running around but you can see most of the damage). Sorry this message is long—I'm still kind of frazzled and my coffee spilled all over my planner this
    "#
  }
  // Header
  @@assert(a1, {{ this.header.claim_id == "CLM-424063" }})
  @@assert(a2, {{ this.header.report_date == "2024-04-22" }})
  @@assert(a2, {{ this.header.incident_date == "2024-04-22" }})
  @@assert(a3, {{ this.header.reported_by == "Jennifer Garcia" }})
  @@assert(a4, {{ this.header.channel == "Email" }})
  // Policy details
  @@assert(a5, {{ this.policy.policy_number == "POL-787532354" }})
  @@assert(a6, {{ this.policy.policyholder_name == "Jennifer Garcia" }})
  @@assert(a7, {{ this.policy.coverage_type == "Property" }})
  @@assert(a8, {{ this.policy.effective_date == "2023-12-20" }})
  @@assert(a9, {{ this.policy.expiration_date == "2024-06-30" }})
  // Insured objects
  @@assert(a10, {{ this.insured_objects[0].object_id == "PROP-656048" }})
  @@assert(a11, {{ this.insured_objects[0].object_type == "Building" }})
  @@assert(a12, {{ this.insured_objects[0].make_model == "Single_Family_Home" }})
  @@assert(a13, {{ this.insured_objects[0].location_address == "6650 Broadway, Georgetown" }})
  // Incident description
  @@assert(a14, {{ this.incident_description.incident_type == "Vandalism " }})
  @@assert(a15, {{ this.incident_description.location_type == "Commercial_Property" }})
  @@assert(a16, {{ this.incident_description.estimated_damage_amount == 5834 }})
  @@assert(a17, {{ this.incident_description.police_report_number == "PR-20250822-4864" }})
}
