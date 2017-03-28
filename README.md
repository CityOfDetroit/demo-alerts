# demo-alerts

Let's send a text message to people when there's going to be a demolition near their house.

## demolitions

From Salesforce, we get:
- planned knock down date
- address
- parcel id

After geocoding the address, we make a Socrata dataset from this, with an additional location field.
