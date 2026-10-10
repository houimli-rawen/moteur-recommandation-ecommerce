-- Schéma de la base ecommerce_rec (à créer avant data.sql)
CREATE TABLE Produit (
    ID SERIAL PRIMARY KEY,
    NomPdt VARCHAR(100),
    Description TEXT,
    Categorie VARCHAR(50),
    Prix NUMERIC(10,2),
    DateAjout DATE
);

CREATE TABLE Users (
    IDUser SERIAL PRIMARY KEY,
    NomUser VARCHAR(50)
);

CREATE TABLE Notes (
    IDUser INT REFERENCES Users(IDUser),
    IDProduit INT REFERENCES Produit(ID),
    Note INT CHECK (Note BETWEEN 1 AND 5),
    DateNote DATE
);

CREATE TABLE SimilariteContenu (
    IDProduit1 INT REFERENCES Produit(ID),
    IDProduit2 INT REFERENCES Produit(ID),
    Score DOUBLE PRECISION,
    PRIMARY KEY (IDProduit1, IDProduit2)
);
