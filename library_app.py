
import streamlit as st

# --------------------- Global Styling --------------------- #
pastel_bg = """
<style>
body {
    background-color: #fffafc;
}
header, .css-18e3th9, .css-1d391kg {
    background-color: #ffe6f2;
}
h1, h2, h3, p {
    color: #663399;
    font-family: 'Comic Sans MS', cursive;
}
.stButton > button {
    color: white;
    background: linear-gradient(to right, #ffb6c1, #dda0dd);
    border-radius: 12px;
    border: none;
    padding: 10px 20px;
}
</style>
"""
st.markdown(pastel_bg, unsafe_allow_html=True)

# --------------------- Classes --------------------- #
class Book:
    def __init__(self, title, author):
        self.title = title
        self.author = author
        self.status = "Available"

class Library:
    def __init__(self):
        self.books = []
        self.borrowed_books = []

    def add_book(self, book):
        self.books.append(book)

    def borrow_book(self, title):
        for book in self.books:
            if book.title.lower() == title.lower():
                if book.status == "Available":
                    book.status = "Not Available"
                    self.borrowed_books.append(book)
                    return f"✅ You've borrowed **{book.title}**!"
                else:
                    return f"⚠️ '{book.title}' is already borrowed."
        return f"❌ '{title}' is not available."

    def return_book(self, title):
        for book in self.borrowed_books:
            if book.title.lower() == title.lower():
                book.status = "Available"
                self.borrowed_books.remove(book)
                return f"✅ Returned '{book.title}' successfully."
        return f"❌ '{title}' wasn't borrowed from here."

    def get_books(self):
        return self.books

    def get_borrowed_books(self):
        return self.borrowed_books

# --------------------- Session Initialization --------------------- #
if "page" not in st.session_state:
    st.session_state.page = "welcome"
if "library" not in st.session_state:
    st.session_state.library = Library()
    sample_books = [
        Book("The Great Gatsby", "F. Scott Fitzgerald"),
        Book("Pride and Prejudice", "Jane Austen"),
        Book("The Catcher in the Rye", "J.D. Salinger"),
        Book("The Hobbit", "J.R.R. Tolkien"),
        Book("Brave New World", "Aldous Huxley")
    ]
    for book in sample_books:
        st.session_state.library.add_book(book)
if "users" not in st.session_state:
    st.session_state.users = {"admin": "admin123"}
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# --------------------- Welcome Page --------------------- #
if st.session_state.page == "welcome":
    st.markdown("<h1 style='text-align:center;'>💖📚 Welcome to Your Magical Library 📚💖</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Organize your books with sparkles and smiles ✨</p>", unsafe_allow_html=True)
    if st.button(" Enter Library"):
        st.session_state.page = "login"
        st.experimental_rerun()

# --------------------- Login / Signup --------------------- #
elif st.session_state.page == "login":
    st.title("🔐 Login or Sign Up")
    tab1, tab2 = st.columns(2)

    with tab1:
        st.subheader("👤 Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username in st.session_state.users and st.session_state.users[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.page = "main"
                st.success(f"Welcome back, {username} 🥰")
                st.experimental_rerun()
            else:
                st.error("Wrong credentials 😥")

    with tab2:
        st.subheader("📝 Sign Up")
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")
        if st.button("Sign Up"):
            if new_user in st.session_state.users:
                st.warning("Username already exists 😬")
            else:
                st.session_state.users[new_user] = new_pass
                st.success("Account created! Please log in 💕")

# --------------------- Main App --------------------- #
elif st.session_state.page == "main":
    nav = st.columns([6, 1, 1, 1, 1])
    nav[1].button("📘 View", on_click=lambda: st.session_state.update({"subpage": "view"}))
    nav[2].button("➕ Add", on_click=lambda: st.session_state.update({"subpage": "add"}))
    nav[3].button("📥 Borrow", on_click=lambda: st.session_state.update({"subpage": "borrow"}))
    nav[4].button("📤 Return", on_click=lambda: st.session_state.update({"subpage": "return"}))

    st.write(f"👋 Hello, **{st.session_state.username}**!")

    lib = st.session_state.library
    subpage = st.session_state.get("subpage", "view")

    if subpage == "view":
        st.subheader("📚 All Books")
        for book in lib.get_books():
            color = "green" if book.status == "Available" else "red"
            st.markdown(f"📖 **{book.title}** by *{book.author}* — "
                        f"<span style='color:{color}'><b>{book.status}</b></span>", unsafe_allow_html=True)

    elif subpage == "add":
        st.subheader("➕ Add a New Book")
        title = st.text_input("Title")
        author = st.text_input("Author")
        if st.button("Add Book"):
            if title and author:
                lib.add_book(Book(title, author))
                st.success(f"'{title}' by {author} added successfully 💖")
            else:
                st.warning("Enter both title and author 📝")

    elif subpage == "borrow":
        st.subheader("📥 Borrow Book")
        title = st.text_input("Which book do you want to borrow?")
        if st.button("Borrow"):
            result = lib.borrow_book(title)
            st.info(result)

    elif subpage == "return":
        st.subheader("📤 Return Book")
        title = st.text_input("Which book are you returning?")
        if st.button("Return"):
            result = lib.return_book(title)
            st.info(result)

    st.markdown("---")
    if st.button("🙏 Exit Library"):
        st.session_state.page = "thankyou"
        st.experimental_rerun()

# --------------------- Thank You Page --------------------- #
elif st.session_state.page == "thankyou":
    st.markdown("<h1 style='text-align:center;'>🌸 Thank You for Visiting! 🌸</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>We hope your day is as lovely as a library full of books 📚💐</p>", unsafe_allow_html=True)
    if st.button("🔁 Go to Welcome Page"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

