import random
import string
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import firebase_admin
from firebase_admin import credentials, db
cred = credentials.Certificate("C:\\Users\\sowky\\Downloads\\project\\word-search-game-f8c47-firebase-adminsdk-fbsvc-5d816e5125.json")
firebase_admin.initialize_app(cred, {'databaseURL': 'https://word-search-game-f8c47-default-rtdb.firebaseio.com/'})

app = Flask(__name__)
app.secret_key = "supersecretkey" 

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True

    def search(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end_of_word

    def starts_with(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True

class Graph:
    def __init__(self, size):
        self.size = size
        self.graph = {}
        self.letters = {}
        self.words = set()

    def add_edge(self, node1, node2):
        """Adds an undirected edge between two nodes."""
        if node1 in self.graph:
            self.graph[node1].append(node2)
        else:
            self.graph[node1] = [node2]

        if node2 in self.graph:
            self.graph[node2].append(node1)
        else:
            self.graph[node2] = [node1]

    def create_grid(self, words):
        """Create a grid with words placed in 8 directions while ensuring overlaps."""
        directions = [(0, 1), (1, 0), (1, 1), (-1, 1), (0, -1), (-1, 0), (-1, -1), (1, -1)]

        # Initialize graph and grid
        for i in range(self.size):
            for j in range(self.size):
                node = (i, j)
                self.graph[node] = []
                self.letters[node] = None  # Initially empty

                # Add edges
                if j + 1 < self.size:
                    self.add_edge(node, (i, j + 1))
                if i + 1 < self.size:
                    self.add_edge(node, (i + 1, j))

        # Place words in the grid
        for word in words:
            word_variants = [word, word[::-1]]
            placed = False
            attempts = 0
            while not placed and attempts < 100:
                row = random.randint(0, self.size - 1)
                col = random.randint(0, self.size - 1)
                dx, dy = random.choice(directions)
                chosen_word = random.choice(word_variants)

                # Check if word fits
                if (0 <= row + dx * (len(chosen_word) - 1) < self.size and
                    0 <= col + dy * (len(chosen_word) - 1) < self.size):

                    positions = [(row + i * dx, col + i * dy) for i in range(len(chosen_word))]

                    if all(self.letters.get(pos) is None or self.letters[pos] == chosen_word[i] 
                           for i, pos in enumerate(positions)):
                        for i, pos in enumerate(positions):
                            self.letters[pos] = chosen_word[i]
                        self.words.add(word)
                        placed = True
                attempts += 1

        # Fill remaining empty spaces
        for node in self.letters:
            if self.letters[node] is None:
                self.letters[node] = random.choice(string.ascii_uppercase)

    def get_grid(self):
        """Returns the grid as a 2D list."""
        return [[self.letters[(i, j)] for j in range(self.size)] for i in range(self.size)]
    
def send_login_email(to_email):
    from_email = "playwellandenjoy@gmail.com"  # Your official email
    app_password = "yvig avdg fwzf ebak"  # Use the App Password generated for Gmail

    subject = "Welcome"
    body = "Play well and enjoy word searching!"

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        # Use SMTP server to send email securely
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.set_debuglevel(1)  # Enable debugging to see more detailed info
            server.starttls()  # Start TLS encryption
            server.login(from_email, app_password)
            response = server.sendmail(from_email, to_email, msg.as_string())
            print("SMTP Response:", response)  # Debugging response
    except Exception as e:
        print("Failed to send email:", e)  # Detailed error message

def generate_grid():
    grid_size = 15
    topic = session.get('topic', 'Fruits')
    difficulty = session.get('difficulty', 'Easy')

    ref = db.reference(f"/word_topics/{topic}/{difficulty}")
    words = ref.get()

    # Clean and uppercase words
    words = [word.strip().upper() for word in words if word.strip()]

    grid = [['' for _ in range(grid_size)] for _ in range(grid_size)]
    word_coords = {}

    directions = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(-1,1),(1,-1)]

    def can_place(word, row, col, dir_x, dir_y):
        for i in range(len(word)):
            r, c = row + i * dir_x, col + i * dir_y
            if not (0 <= r < grid_size and 0 <= c < grid_size):
                return False
            if grid[r][c] not in ('', word[i]):
                return False
        return True

    def place_word(word):
        attempts = 100
        while attempts > 0:
            dir_x, dir_y = random.choice(directions)
            row = random.randint(0, grid_size - 1)
            col = random.randint(0, grid_size - 1)

            if can_place(word, row, col, dir_x, dir_y):
                coords = []
                for i in range(len(word)):
                    r, c = row + i * dir_x, col + i * dir_y
                    grid[r][c] = word[i]
                    coords.append([r, c])
                word_coords[word] = coords
                return True
            attempts -= 1
        return False

    for word in words:
        place_word(word)

    # Fill empty cells
    for row in range(grid_size):
        for col in range(grid_size):
            if grid[row][col] == '':
                grid[row][col] = chr(random.randint(65, 90))  # A-Z

    return grid, words, word_coords

@app.route('/')
def index():
    return render_template('namepage.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        user_ref = db.reference(f"users/{username}")
        if user_ref.get():
            error = "Username already exists"
        else:
            user_ref.set({"password": password, "email": email})
            return redirect(url_for('login'))
    return render_template('sign_up.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_ref = db.reference(f"users/{username}")
        user_data = user_ref.get()
        if user_data and user_data['password'] == password:
            session['username'] = username
            user_email = user_data.get("email")
            if user_email:
                send_login_email(user_email)
            return redirect(url_for('topic_selection'))
        else:
            error = "Invalid credentials"
    return render_template('sign_in.html')

@app.route('/topic_selection', methods=['GET'])
def topic_selection():
    return render_template('topic_selection.html')

@app.route('/select-difficulty', methods=['POST'])
def select_difficulty():
    topic = request.form['topic']
    session['topic'] = topic
    return render_template('diff_level.html', topic=topic)

@app.route('/start-game', methods=['POST'])
def start_game():
    session['difficulty'] = request.form['difficulty']
    return redirect(url_for('generate_grid'))

@app.route('/generate-grid', methods=['GET', 'POST'])
def generate_grid():
    grid_size = 15
    topic = session.get('topic', 'Fruits')
    difficulty = session.get('difficulty', 'Easy')
    
    # Fetch words from the database
    ref = db.reference(f"/word_topics/{topic}/{difficulty}")
    words = ref.get()

    # Initialize word_coords dictionary
    word_coords = {}

    # If words exist, randomly select based on difficulty
    if words:
        if difficulty == 'Easy':
            selected_words = random.sample(words, 5)  # Pick any 5 words randomly
        elif difficulty == 'Medium':
            selected_words = random.sample(words, 10)  # Pick any 10 words randomly
        elif difficulty == 'Hard':
            selected_words = random.sample(words, 15)  # Pick any 15 words randomly
        else:
            selected_words = words  # Default to all words if difficulty is unknown

        # Uppercase the selected words
        selected_words = [word.upper() for word in selected_words]
    else:
        # Default list of words if no words found in database
        selected_words = ["PYTHON", "JAVA", "AI", "GRAPH", "MACHINE", "CODE", "LOGIC"]

    # Initialize Trie and Graph
    trie = Trie()
    for word in selected_words:
        trie.insert(word)

    # Create the grid with the selected words
    g = Graph(size=grid_size)
    g.create_grid(selected_words)
    grid = g.get_grid()

    # Return the grid to the template with word_coords
    return render_template(
        "samp_grid.html", 
        grid=grid, 
        words=selected_words, 
        topic=topic, 
        difficulty=difficulty, 
        word_coords=word_coords  # Ensure word_coords is passed here
    )

@app.route('/validate-word', methods=['POST'])
def validate_word():
    word = request.json.get('word').upper()
    topic = session.get('topic', 'Fruits')
    difficulty = session.get('difficulty', 'Easy')
    ref = db.reference(f"/word_topics/{topic}/{difficulty}")
    words = ref.get()
    trie = Trie()
    if words:
        for w in words:
            trie.insert(w.upper())
    return jsonify(valid=trie.search(word))

@app.route('/results')
def results():
    if 'username' not in session:
        return redirect(url_for('login'))
    words_found = request.args.get('words_found', default=0, type=int)
    total_words = request.args.get('total_words', default=7, type=int)
    time_used = request.args.get('time_used', default=0, type=int)
    topic = session.get('topic', 'Fruits')
    difficulty = session.get('difficulty', 'Easy')

    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    username = session['username']
    game_ref = db.reference(f"users/{username}/game_history").push({
        'topic': topic,
        'difficulty': difficulty,
        'words_found': words_found,
        'total_words': total_words,
        'time_used': time_used,
        'date': current_date,
        'time': current_time
    })
    return render_template('results.html',
                           words_found=words_found,
                           total_words=total_words,
                           time_used=time_used,
                           topic=topic,
                           difficulty=difficulty,
                           date=now.strftime("%Y-%m-%d"),
                           time=now.strftime("%H:%M:%S"))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5002, debug=True)

