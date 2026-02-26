import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(page_title="Library Analytics", layout="wide")

st.markdown("""
<style>
.block-container { max-width: 1200px; padding-top: 2rem; }
.rec-card {
    background:#0f172a;
    border:1px solid #1f2937;
    border-radius:12px;
    padding:1rem 1.3rem;
    margin-bottom:1rem;
}
.badge { font-size:0.85rem; color:#93c5fd; }
</style>
""", unsafe_allow_html=True)

st.title("📚 Library Analytics & Recommendation System")

# ==================================================
# SESSION STATE
# ==================================================
if "db_ready" not in st.session_state:
    st.session_state.db_ready = False
if "active_user" not in st.session_state:
    st.session_state.active_user = None

# ==================================================
# DATABASE
# ==================================================
@st.cache_resource
def get_conn():
    return sqlite3.connect("library.db", check_same_thread=False)

conn = get_conn()
cur = conn.cursor()

# ==================================================
# ONE-TIME DB INIT (SAFE)
# ==================================================
if not st.session_state.db_ready:
    cur.execute("DROP TABLE IF EXISTS transactions")
    cur.execute("DROP TABLE IF EXISTS books")
    cur.execute("DROP TABLE IF EXISTS users")

    cur.execute("""
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE
    )""")

    cur.execute("""
    CREATE TABLE books (
        book_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        genre TEXT
    )""")

    cur.execute("""
    CREATE TABLE transactions (
        tx_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        book_id INTEGER,
        action TEXT,
        timestamp TEXT
    )""")

    BOOKS = [
        ("1984","Dystopian"),("Brave New World","Dystopian"),
        ("Fahrenheit 451","Dystopian"),("The Handmaid's Tale","Dystopian"),
        ("Animal Farm","Dystopian"),
        ("The Hobbit","Fantasy"),("The Lord of the Rings","Fantasy"),
        ("Harry Potter","Fantasy"),("Mistborn","Fantasy"),
        ("The Name of the Wind","Fantasy"),("Wheel of Time","Fantasy"),
        ("Clean Code","Tech"),("Design Patterns","Tech"),
        ("The Pragmatic Programmer","Tech"),("Refactoring","Tech"),
        ("Introduction to Algorithms","Tech"),
        ("Artificial Intelligence","Tech"),("Deep Learning","Tech"),
        ("Dune","Science Fiction"),("Foundation","Science Fiction"),
        ("Neuromancer","Science Fiction"),("Snow Crash","Science Fiction"),
        ("The Martian","Science Fiction"),
        ("A Brief History of Time","Science"),("Cosmos","Science"),
        ("Sapiens","History"),("Homo Deus","History")
    ]

    cur.executemany("INSERT INTO books VALUES (NULL,?,?)", BOOKS)
    conn.commit()
    st.session_state.db_ready = True

# ==================================================
# SIDEBAR
# ==================================================
st.sidebar.markdown("### 👤 User Session")
username_input = st.sidebar.text_input("Enter your name")

if st.sidebar.button("Create / Select User"):
    if username_input.strip():
        cur.execute("INSERT OR IGNORE INTO users (username) VALUES (?)",
                    (username_input.strip(),))
        conn.commit()

users_df = pd.read_sql("SELECT * FROM users", conn)
if users_df.empty:
    st.warning("Create a user to continue.")
    st.stop()

user_id = st.sidebar.selectbox(
    "Active user",
    users_df["user_id"],
    index=0 if st.session_state.active_user is None else
    list(users_df["user_id"]).index(st.session_state.active_user),
    format_func=lambda x: users_df.set_index("user_id").loc[x, "username"]
)
st.session_state.active_user = user_id

st.sidebar.markdown("---")
show_explanations = st.sidebar.toggle("🧠 Explain recommendations", value=False)

page = st.sidebar.radio("Navigation", ["📚 Library", "📊 Insights", "🤖 Recommendations"])

# ==================================================
# LOAD DATA
# ==================================================
books_df = pd.read_sql("SELECT * FROM books", conn)
tx_df = pd.read_sql("SELECT * FROM transactions", conn)

# ==================================================
# BORROW STATE
# ==================================================
def get_borrowed_books(uid):
    state = {}
    for _, r in tx_df[tx_df.user_id == uid].iterrows():
        state[r.book_id] = r.action
    return {b for b,a in state.items() if a == "borrow"}

borrowed = get_borrowed_books(user_id)

# ==================================================
# 📚 LIBRARY
# ==================================================
if page == "📚 Library":
    st.subheader("Library Collection")

    for _, book in books_df.iterrows():
        c1,c2,c3,c4 = st.columns([4,2,2,2])
        c1.write(f"**{book.title}**")
        c2.write(book.genre)

        if book.book_id in borrowed:
            c3.markdown("🟡 **Borrowed**")
            if c4.button("Return", key=f"r{book.book_id}"):
                cur.execute("INSERT INTO transactions VALUES (NULL,?,?, 'return',?)",
                            (user_id, book.book_id, datetime.now().isoformat()))
                conn.commit()
                st.rerun()
        else:
            c3.markdown("🟢 **Available**")
            if c4.button("Borrow", key=f"b{book.book_id}"):
                cur.execute("INSERT INTO transactions VALUES (NULL,?,?, 'borrow',?)",
                            (user_id, book.book_id, datetime.now().isoformat()))
                conn.commit()
                st.rerun()

# ==================================================
# 📊 INSIGHTS
# ==================================================
elif page == "📊 Insights":
    st.subheader("Reading Insights")

    borrows = tx_df[tx_df.action=="borrow"]
    if borrows.empty:
        st.info("No borrowing activity yet.")
    else:
        top = borrows.groupby("book_id").size().sort_values(ascending=False).head(8)
        titles = books_df.set_index("book_id").loc[top.index]["title"]
        st.bar_chart(titles.value_counts())

# ==================================================
# 🤖 RECOMMENDATIONS
# ==================================================
elif page == "🤖 Recommendations":
    st.subheader("🎯 Recommended for You")

    borrows = tx_df[tx_df.action=="borrow"]
    if borrows.empty:
        st.info("Borrow books to activate recommendations.")
        st.stop()

    interaction = borrows.pivot_table(
        index="user_id", columns="book_id",
        values="tx_id", aggfunc="count", fill_value=0
    )

    explanations = {}
    fav_genres = []

    if interaction.loc[user_id].sum() == 0:
        popular = borrows.groupby("book_id").size().sort_values(ascending=False).head(6)
        recs = books_df.set_index("book_id").loc[popular.index]
        for bid in recs.index:
            explanations[bid] = "🔥 Popular among readers"

    else:
        sim = cosine_similarity(interaction)
        sim_df = pd.DataFrame(sim, interaction.index, interaction.index)

        scores = pd.Series(0, index=interaction.columns)
        for u in sim_df[user_id].drop(user_id).index:
            scores += sim_df.loc[user_id,u] * interaction.loc[u]

        scores[interaction.loc[user_id] > 0] = 0
        top_ids = scores.sort_values(ascending=False).head(6).index
        recs = books_df.set_index("book_id").loc[top_ids]

        user_books = borrows[borrows.user_id==user_id]["book_id"]
        fav_genres = books_df.set_index("book_id").loc[user_books]["genre"].value_counts().index.tolist()

        for bid,row in recs.iterrows():
            explanations[bid] = "👥 Similar readers" + \
                (" · 📘 Genre match" if row.genre in fav_genres else "")

    for bid,row in recs.iterrows():
        st.markdown('<div class="rec-card">', unsafe_allow_html=True)
        st.markdown(f"### {row.title}")
        st.caption(f"Genre: {row.genre}")

        if show_explanations:
            st.markdown(f"<span class='badge'>{explanations.get(bid)}</span>",
                        unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

