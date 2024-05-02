import argparse
from arango import ArangoClient
import base64
from dotenv import load_dotenv
import os

load_dotenv()

def startConnection() -> ArangoClient:
    encodedCA = os.getenv('ARANGO_CA')
    try:
        file_content = base64.b64decode(encodedCA)
        with open("cert_file.crt", "w+") as f:
            f.write(file_content.decode("utf-8"))
    except Exception as e:
        print(str(e))
        exit(1)

    client = ArangoClient(
        hosts=os.getenv('ARANGO_HOST'), verify_override="cert_file.crt"
    )

    print("Succesfull Conection to ArangoDB!")
    
    return client

def connectToDatabase(client: ArangoClient):
    try:
        db = client.db("test", username=os.getenv('ARANGO_USERNAME'), password=os.getenv('ARANGO_PASSWORD'))
        db.properties()
        return db
    except Exception as e:
        if "database not found" in str(e):
            print("Database not found")
        exit(1)

def createAndSeedDatabase(client: ArangoClient):
    sys_db = client.db("_system", username=os.getenv('ARANGO_USERNAME'), password=os.getenv('ARANGO_PASSWORD'))
    sys_db.create_database("test")
    db = client.db("test", username=os.getenv('ARANGO_USERNAME'), password=os.getenv('ARANGO_PASSWORD'))
    
    students = db.create_collection("students")
    students.add_persistent_index(fields=["name"], unique=True)
    students.insert({"name": "jane", "age": 39})
    students.insert({"name": "josh", "age": 18})
    students.insert({"name": "judy", "age": 21})


def main():
    parser = argparse.ArgumentParser(description='Connect to Arango.')
    parser.add_argument('--new', 
                        action='store_true',
                        help='create db and seed it')
    args = parser.parse_args()

    try:
        client = startConnection()
        if args.new:
            print("Creating new database")
            createAndSeedDatabase(client)        
        db = connectToDatabase(client)
    except Exception as e:
        print("Error connecting to the database:", str(e))
        exit(1)
    
    runningFlag = True
    while runningFlag:
        print("\nTest ArangoDB:")
        print("1. Add a new student")
        print("2. List all students")
        print("3. Exit")
        option = input("Choose an option: ")

        if option == "1":
            print("Adding a new student")
            studentName = input("Enter the student's name: ")
            studentAge = int(input("Enter the student's age: "))
            try:
                db.collection("students").insert({"name": studentName, "age": studentAge})
                print("Student added successfully!")
            except Exception as e:
                print("Error adding student:", str(e))
        elif option == "2":
            try:
                cursor = db.aql.execute("FOR doc IN students RETURN doc")
                student_names = [document["name"] for document in cursor]
                print("Students:")
                for student in student_names:
                    print(student)
            except Exception as e:
                print("Error listing students:", str(e), "\n")
        elif option == "3":
            runningFlag = False
        else:
            print("Invalid option") 

main()

CLASSES = {
    "MAT101": "Calculus",
    "STA101": "Statistics",
    "CSC101": "Algorithms",
}

STUDENTS = {
    "01": "Anna Smith",
    "02": "Jake Clark",
    "03": "Lisa Jones",
}