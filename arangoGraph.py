import argparse
from arango import ArangoClient
import base64
from dotenv import load_dotenv
import os

load_dotenv()

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
        db = client.db("esau", username=os.getenv('ARANGO_USERNAME'), password=os.getenv('ARANGO_PASSWORD'))
        db.properties()
        return db
    except Exception as e:
        if "database not found" in str(e):
            print("Database not found")
        exit(1)

def createAndSeedDatabase(client: ArangoClient):
    db = client.db("esau", username=os.getenv('ARANGO_USERNAME'), password=os.getenv('ARANGO_PASSWORD'))

    # Create a new graph named "school".
    graph = db.create_graph("school")

    # Create vertex collections for the graph.
    students = graph.create_vertex_collection("students")
    lectures = graph.create_vertex_collection("lectures")

    # Create an edge definition (relation) for the graph.
    edges = graph.create_edge_definition(
        edge_collection="register",
        from_vertex_collections=["students"],
        to_vertex_collections=["lectures"]
    )

    # Insert vertex documents into "students" (from) vertex collection.
    students.insert({"_key": "01", "full_name": "Anna Smith"})
    students.insert({"_key": "02", "full_name": "Jake Clark"})
    students.insert({"_key": "03", "full_name": "Lisa Jones"})

    # Insert vertex documents into "lectures" (to) vertex collection.
    lectures.insert({"_key": "MAT101", "title": "Calculus"})
    lectures.insert({"_key": "STA101", "title": "Statistics"})
    lectures.insert({"_key": "CSC101", "title": "Algorithms"})

    # Insert edge documents into "register" edge collection.
    edges.insert({"_from": "students/01", "_to": "lectures/MAT101"})
    edges.insert({"_from": "students/01", "_to": "lectures/STA101"})
    edges.insert({"_from": "students/01", "_to": "lectures/CSC101"})
    edges.insert({"_from": "students/02", "_to": "lectures/MAT101"})
    edges.insert({"_from": "students/02", "_to": "lectures/STA101"})
    edges.insert({"_from": "students/03", "_to": "lectures/CSC101"})

def existingRegistration(db: ArangoClient.db, student_id, class_id):
    # Get the edge collection
    edges = db.collection('register')

    # Define the nodes
    from_node = f"students/{student_id}"
    to_node = f"lectures/{class_id}"

    # Find the edge
    edgeCursor = edges.find({"_from": from_node, "_to": to_node}, limit=1)
    
    if edgeCursor:
        for edge in edgeCursor:
            return edge["_key"]
    else: 
        return None

def enrollStudent(db: ArangoClient.db, student_id, class_id):
    if existingRegistration(db, student_id, class_id):
        print("Student already enrolled in class")
        return
    try:
        edges = db.collection('register')
        edges.insert({"_from": "students/"+student_id, "_to": "lectures/"+class_id})
        print("Student added successfully!")
    except Exception as e:
        print("Error enrolling student:", str(e))
        
def unenrollStudent(db: ArangoClient.db, student_id, class_id):
    edge_key = existingRegistration(db, student_id, class_id)
    if not edge_key:
        print("Student wasn't enrolled in class")
        return
    try:
        edges = db.collection('register')
        edges.delete(edge_key)    
        print("Student removed successfully!")
    except Exception as e:
        print("Error unenrolling student:", str(e))

def listStudentsClasses(db: ArangoClient.db, student_id):
    try:
        query = f"""
        FOR v, e, p IN 1..3 OUTBOUND 'students/{student_id}' GRAPH 'school'
        OPTIONS {{ bfs: true, uniqueVertices: 'global' }}
        RETURN v
        """
        cursor = db.aql.execute(query)
        return [document['title'] for document in cursor]
            
    except Exception as e:
        print("Error listing student's classes:", str(e))

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
        print("1. Enroll in class")
        print("2. Unenroll from class")
        print("3. List student's classes")
        print("4. Exit")
        option = input("Choose an option: ")

        if option == "1":
            print("Enroll in class")
            print(STUDENTS)
            studentId = input("Type student's ID: ")
            print(CLASSES)
            classId = input("Type classes' ID: ")
            try:
                enrollStudent(db, studentId, classId)
            except Exception as e:
                print("Error adding student:", str(e))
        if option == "2":
            print("Unenroll from class")
            print(STUDENTS)
            studentId = input("Type student's ID: ")
            print(CLASSES)
            classId = input("Type classes' ID: ")
            try:
                unenrollStudent(db, studentId, classId)
            except Exception as e:
                print("Error removing student:", str(e))
        if option == "3":
            print("List students classes")
            print(STUDENTS)
            studentId = input("Type student's ID: ")
            try:
                classes = listStudentsClasses(db, studentId)
                print("Classes: ", classes)
            except Exception as e:
                print("Error listing students classes:", str(e))
        elif option == "4":
            runningFlag = False

main()
