class PersonNameAndTitle {
    family string? @alias("surname") @description("Surname of the patient")
    given string[]? @alias("givenName") @description("Given name(s) of the patient")
    prefix string? @alias("title") @description("Title of the patient")
}

enum MaritalStatus {
    Married
    Divorced
    Widowed
    NeverMarried
}

class Address {
    line string
    city string
    state string
    postalCode string?
    country "US" | null
}

class Patient {
  name PersonNameAndTitle | null @alias("patientNameAndTitle")
  age int?
  gender "Male" | "Female" | null
  birthDate string?  @description("Date of birth of the patient in ISO-8601 format")
  address Address | null @alias("homeAddress")  @description("Residence address of the patient")
  phone string?
  email string?
  maritalStatus MaritalStatus | null
  primaryLanguage "English" | "Spanish" | null
  allergy Allergy[]?
}

class Practitioner {
  name PersonNameAndTitle | null @alias("practitionerNameAndTitle")
  address Address | null @alias("practitionerAddress")
  phone string?
  email string?
}

class Immunization {
    traits string[]? @alias("vaccineTraits") @description("Text describing the name and traits of the immunization")
    status "completed" | null
    occurrenceDateTime string?  @description("ISO-8601 format for datetime including timezone")
}

class Substance {
    category "environment" | "food" | "medication" | "other"
    name string?
    manifestation string[]?  @description("Text describing the manifestation of the allergy or intolerance")
}

class Allergy {
    substance Substance[] | null @description("The substance that the patient is allergic to")
}

// --- Functions ---

function ExtractPatient(record: string) -> Patient {
  client OpenRouterGoogleGemini2Flash
  prompt #"
    Extract the patient information from the given note.
    - Do not infer any information that is not explicitly mentioned in the text.
    - If you are unsure about any field, leave it as None.
    
    {{ ctx.output_format }}

    {{ _.role('user') }}

    {{ record }}
  "#
}

function ExtractPractitioner(record: string) -> Practitioner[] {
  client OpenRouterGoogleGemini2Flash
  prompt #"
    Extract practitioner & healthcare provider information from the given note.
    - Do not infer any information that is not explicitly mentioned in the text.
    - If you are unsure about any field, leave it as None.

    {{ ctx.output_format }}

    {{ _.role('user') }}

    {{ record }}
  "#
}

function ExtractImmunization(record: string) -> Immunization[] {
  client OpenRouterGoogleGemini2Flash
  prompt #"
    Extract immunization information from the given note.
    - Do not infer any information that is not explicitly mentioned in the text.
    - If you are unsure about any field, leave it as None.

    {{ ctx.output_format }}

    {{ _.role('user') }}

    {{ record }}
  "#
}

// --- Tests ---

test ExtractPatient1 {
  functions [ExtractPatient]
  args {
    record #"
    This is about Mr. Fernando Amos Breitenberg. He's married. Now let's talk about his medical encounters.\n\nThe main one is a well child visit. This happened at the clinic. The visit started on December 23, 1992, at 01:08:42 and ended on the same day at 01:23:42, with timezone being +01:00. Mr. Breitenberg was looked after by Dr. Trent Krajcik. He was the one who did the whole procedure.\n\nMoving on, Mr. Breitenberg has an allergy. It's active and confirmed. He's allergic to shellfish. We've known this since April 2, 1994, at 12:08:42, with timezone as +02:00.\n\nFinally, all this happened at our healthcare provider in Quincy. It's located at 300 CONGRESS ST STE 203, Quincy, MA, 021690907, US.
    "#
  }
  @@assert(family_name, {{ this.name.family == "Breitenberg" }})
  @@assert(given_name, {{ "Fernando" in this.name.given }})
  @@assert(given_name, {{ "Amos" in this.name.given }})
  @@assert(title, {{ this.name.prefix == "Mr." }})
  @@assert(marital_status, {{ this.maritalStatus == "Married" }})
  @@assert(birth_date, {{ this.birthDate == none }})
  @@assert(allergy_exists, {{ this.allergy[0].substance[0].name == "shellfish" }})
}

test ExtractPatient2 {
  functions [ExtractPatient]
  args {
    record #"
    Ms. Marisol Rodríguez, who was born on December 1, 1995, and resides at her home at 547 Effertz Extension Unit 28, East Longmeadow, Massachusetts, 00000, is never married. She identifies Spanish as her primary language. She can be reached at her home phone number, which is 555-808-5474.\n\nIn the past, Marisol visited the ENCOMPASS HEALTH REHAB HOSPITAL OF WESTERN MASS on December 13, 2013, from 9:15:24 until 9:30:24 in Central European Standard Time for a postnatal visit. During this visit, Dr. Cletus Paucek, a primary performer, was the practitioner managing her care. You may reach out to Dr. Paucek at his work email, which is Cletus494.Paucek755@example.com.\n\nOf note, Marisol has a confirmed low criticality allergy towards shellfish, first noted on June 2, 1997, at 22:15:24 in Central Eastern Standard Time. Reactions to an exposure to shellfish in her case have varied. In some instances, she experiences a moderate eruption of skin. In severe cases, she has experienced anaphylaxis. More often, her symptoms are mild and include itching and coughing. Another noted allergy intolerance is currently active, yet the clinical details are not specified here.\n\nIn conclusion, based on the documented clinical data, Marisol has a history of postnatal follow-ups and confirmed food allergies that need to be managed, particularly regarding shellfish. She has also had encounters with a primary care practitioner, Dr. Paucek, who can be contacted for more in-depth knowledge about her medical history. The active allergy intolerance should also be further investigated for better management.\n\n
    "#
  }
  @@assert(family_name, {{ this.name.family == "Rodríguez" }})
  @@assert(given_name, {{ "Marisol" in this.name.given }})
  @@assert(title, {{ this.name.prefix == "Ms." }})
  @@assert(birth_date, {{ this.birthDate == "1995-12-01" }})
  @@assert(address_line, {{ this.address.line == "547 Effertz Extension Unit 28" }})
  @@assert(address_city, {{ this.address.city == "East Longmeadow" }})
  @@assert(address_state, {{ this.address.state == "Massachusetts" }})
  @@assert(address_postal_code, {{ this.address.postalCode == "00000" }})
  @@assert(address_country, {{ this.address.country == "US" }})
  @@assert(phone, {{ this.phone == "555-808-5474" }})
  @@assert(primary_language, {{ this.primaryLanguage == "Spanish" }})
  @@assert(marital_status, {{ this.maritalStatus == "NeverMarried" }})
  @@assert(allergy_exists, {{ this.allergy[0].substance[0].name == "shellfish" }})
}

test ExtractPatient3 {
  functions [ExtractPatient]
  args {
    record #"
    Patient Information:\n- Full Name: Officially named Azucena Lore Durgan \n- Gender: Female\n- Date of Birth: October 20, 2008\n- Marital Status: Never Married\n\nContact Details:\n- Contact Number: Home phone is 555-374-5890\n- Address: Lives at 599 Ledner Park, Lowell, Massachusetts, 01850, US\n\nOther Information:\n- Primary Language: English (United States)\n\n
    "#
  }
  @@assert(family_name, {{ this.name.family == "Durgan" }})
  @@assert(given_name, {{ "Azucena" in this.name.given }})
  @@assert(given_name, {{ "Lore" in this.name.given }})
  @@assert(title, {{ this.name.prefix == none }})
  @@assert(gender, {{ this.gender == "Female" }})
  @@assert(birth_date, {{ this.birthDate == "2008-10-20" }})
  @@assert(marital_status, {{ this.maritalStatus == "NeverMarried" }})
  @@assert(primary_language, {{ this.primaryLanguage == "English" }})
  @@assert(allergy_does_not_exist, {{ this.allergy == none }})
}

test ExtractPractitioner1 {
  functions [ExtractPractitioner]
  args {
    record #"
    This is about Mr. Fernando Amos Breitenberg. He's married. Now let's talk about his medical encounters.\n\nThe main one is a well child visit. This happened at the clinic. The visit started on December 23, 1992, at 01:08:42 and ended on the same day at 01:23:42, with timezone being +01:00. Mr. Breitenberg was looked after by Dr. Trent Krajcik. He was the one who did the whole procedure.\n\nMoving on, Mr. Breitenberg has an allergy. It's active and confirmed. He's allergic to shellfish. We've known this since April 2, 1994, at 12:08:42, with timezone as +02:00.\n\nFinally, all this happened at our healthcare provider in Quincy. It's located at 300 CONGRESS ST STE 203, Quincy, MA, 021690907, US.
    "#
  }
  @@assert(family_name, {{ this.name.family == "Krajcik" }})
  @@assert(given_name, {{ "Trent" in this.name.given }})
  @@assert(title, {{ this.name.prefix == "Dr." }})
  @@assert(address_line, {{ this.address.line == "300 CONGRESS ST STE 203" }})
  @@assert(address_city, {{ this.address.city == "Quincy" }})
  @@assert(address_state, {{ this.address.state == "MA" }})
  @@assert(address_postal_code, {{ this.address.postalCode == "021690907" }})
  @@assert(address_country, {{ this.address.country == "US" }})
}

test ExtractPractitioner2 {
  functions [ExtractPractitioner]
  args {
    record #"
    Ms. Marisol Rodríguez, who was born on December 1, 1995, and resides at her home at 547 Effertz Extension Unit 28, East Longmeadow, Massachusetts, 00000, is never married. She identifies Spanish as her primary language. She can be reached at her home phone number, which is 555-808-5474.\n\nIn the past, Marisol visited the ENCOMPASS HEALTH REHAB HOSPITAL OF WESTERN MASS on December 13, 2013, from 9:15:24 until 9:30:24 in Central European Standard Time for a postnatal visit. During this visit, Dr. Cletus Paucek, a primary performer, was the practitioner managing her care. You may reach out to Dr. Paucek at his work email, which is Cletus494.Paucek755@example.com.\n\nOf note, Marisol has a confirmed low criticality allergy towards shellfish, first noted on June 2, 1997, at 22:15:24 in Central Eastern Standard Time. Reactions to an exposure to shellfish in her case have varied. In some instances, she experiences a moderate eruption of skin. In severe cases, she has experienced anaphylaxis. More often, her symptoms are mild and include itching and coughing. Another noted allergy intolerance is currently active, yet the clinical details are not specified here.\n\nIn conclusion, based on the documented clinical data, Marisol has a history of postnatal follow-ups and confirmed food allergies that need to be managed, particularly regarding shellfish. She has also had encounters with a primary care practitioner, Dr. Paucek, who can be contacted for more in-depth knowledge about her medical history. The active allergy intolerance should also be further investigated for better management.\n\n
    "#
  }
  @@assert(family_name, {{ this.name.family == "Paucek" }})
  @@assert(given_name, {{ "Cletus" in this.name.given }})
  @@assert(title, {{ this.name.prefix == "Dr." }})
  @@assert(email, {{ this.email == "Cletus494.Paucek755@example.com" }})
}

test ExtractImmunization1 {
  functions [ExtractImmunization]
  args {
    record #"
    A clinical note for Ms. Sonia María Bañuelos: \n\nOn December 24, 2013, at 16:59:45 GMT+1, Ms. Bañuelos received an injectable, preservative-free, seasonal influenza vaccine. This immunization procedure was completed smoothly. \n\nRegarding her personal information, Ms. Bañuelos, identifies as female and is not a multiple birth individual, meaning she doesn't have any twins or triplets. The patient also received a chicken pox vaccine on Jan 23rd, 2014. Her official residence is listed as 130 Rempel Vale, Boston, Massachusetts, 02111, United States. Moreover, it's noted that her primary language is Spanish. Hence, all communication with her should ideally be in Spanish for ensuring comprehension.\n\n\n
    "#
  }
  @@assert(occurrence_date_time, {{ this[0].occurrenceDateTime == "2013-12-24T16:59:45+01:00" }})
  @@assert(status, {{ this[0].status == "completed" }})
}
