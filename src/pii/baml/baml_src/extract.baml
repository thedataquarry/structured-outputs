class Pii {
  ACCOUNTNAME string | null
  ACCOUNTNUMBER string | null
  AGE string | null
  AMOUNT string | null
  BIC string | null
  BITCOINADDRESS string | null
  BUILDINGNUMBER string | null
  CITY string | null
  COMPANYNAME string | null
  COUNTY string | null
  CREDITCARDCVV string | null
  CREDITCARDISSUER string | null
  CREDITCARDNUMBER string | null
  CURRENCY string | null
  CURRENCYCODE string | null
  CURRENCYNAME string | null
  CURRENCYSYMBOL string | null
  DATE string | null
  DOB string | null
  EMAIL string | null
  ETHEREUMADDRESS string | null
  EYECOLOR string | null
  FIRSTNAME string | null
  GENDER string | null
  HEIGHT string | null
  IBAN string | null
  IP string | null
  IPV4 string | null
  IPV6 string | null
  JOBAREA string | null
  JOBTITLE string | null
  JOBTYPE string | null
  LASTNAME string | null
  LITECOINADDRESS string | null
  MAC string | null
  MASKEDNUMBER string | null
  MIDDLENAME string | null
  NEARBYGPSCOORDINATE string | null
  ORDINALDIRECTION string | null
  PASSWORD string | null
  PHONEIMEI string | null
  PHONENUMBER string | null
  PIN string | null
  PREFIX string | null
  SECONDARYADDRESS string | null
  SEX string | null
  SSN string | null  @description("Can occur in formats like 123-45-6789 or 123.45.6789")
  STATE string | null
  STREET string | null
  TIME string | null
  URL string | null
  USERAGENT string | null
  USERNAME string | null
  VEHICLEVIN string | null
  VEHICLEVRM string | null
  ZIPCODE string | null
}

function ExtractPii(text: string) -> Pii {
  client OpenRouterGoogleGemini3Flash
  prompt #"
    Extract structured information about PII entities from the text provided by the user.
    - If you are unsure about a field, leave it as null.

    {{ ctx.output_format }}

    {{ _.role("user") }}
    {{ text }}
  "#
}

test test_1 {
  functions [ExtractPii]
  args {
    text #"
    To clarify child support arrangements, we require information on all assets including bank account Investment Account with number 32944548 and any Bitcoin address such as 1Mw9PZZmKzyoyFXeiSwa732B5Qrzy2.
    "#
  }
  @@assert(a1, {{ this.ACCOUNTNAME == "Investment Account" }})
  @@assert(a2, {{ this.ACCOUNTNUMBER == "32944548" }})
  @@assert(a3, {{ this.BITCOINADDRESS == "1Mw9PZZmKzyoyFXeiSwa732B5Qrzy2" }})
}

test test_2 {
  functions [ExtractPii]
  args {
    text #"
    Despite offering numerous interventions, Manley(756.9342.5804) has consistently neglected academic responsibilities and disrupted class atmosphere by using online platforms without permission during classes (discovered through 9aee:bced:de62:9ea5:6064:99d3:5ffa:cb0a Tracking)
    "#
  }
  @@assert(a1, {{ this.FIRSTNAME == "Manley" }})
  @@assert(a2, {{ this.IP == "9aee:bced:de62:9ea5:6064:99d3:5ffa:cb0a" }})
  @@assert(a3, {{ this.SSN == "756.9342.5804" }})
}