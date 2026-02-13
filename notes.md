- Everyone
  - auth
    - /token :: login
  - users
    - / :: create user
  - categories
    - / :: read categories
    - /{category_id}/products :: read category products
  - products
    - / :: read products
    - /{product_id} :: read product
    - /{product_id}/reviews :: read product reviews
- Current User
  - auth
    - /refresh :: refresh your access token
    - /logout :: remove your access token
  - users
    - /me :: read your info
  - categories
  - products
    - **seller**
      - / :: create product
      - /{product_id} :: update your product
    

## Public

- auth
  - /token :: login
- users
  /      - craete user
categories
  / - read categories
  /{category_id}/products - read category products
products
  

## Logged In

auth
  /refresh - refresh your access token
  /logout - remove your access token
users
  /me - get your info
