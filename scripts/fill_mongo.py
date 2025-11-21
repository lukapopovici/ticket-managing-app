import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["pos_client"]
    clients = db["clients"]
    await clients.delete_many({})
    docs = [
        {
            "email": "alice@example.com",
            "prenume": "Alice",
            "nume": "Popescu",
            "public": True,
            "social": ["https://facebook.com/alice"],
            "bilete": [
                {"cod": "TICKET1", "tip": "eveniment", "eveniment": {"nume": "Concert Rock", "locatie": "Sala Polivalenta"}},
                {"cod": "TICKET2", "tip": "pachet", "pachet": {"nume": "Pachet Cultura"}}
            ]
        },
        {
            "email": "bob@example.com",
            "prenume": "Bob",
            "nume": "Ionescu",
            "public": False,
            "social": ["https://twitter.com/bob"],
            "bilete": [
                {"cod": "TICKET3", "tip": "eveniment", "eveniment": {"nume": "Conferinta IT", "locatie": "Hotel Central"}}
            ]
        }
    ]
    await clients.insert_many(docs)
    print("MongoDB filled!")

if __name__ == "__main__":
    asyncio.run(main())
