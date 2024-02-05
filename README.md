# Important
This program was written in Python3.11->It does not work on the latest version of Python and other versions are untested. 

# Setup
1. Download [Python 3.11](https://www.python.org/downloads/release/python-3110/) if you don't already have it
2. Set shebang line to python interpreter location.
3. Download requirements with pip, `pip3 install -r requirements.txt`
4. Sign up for a [pinecone API key]([url](https://www.pinecone.io/)
5. Run the program and have fun! 

# BabyAGI4free
A clone of BabyAGI that utilizes g4f (for gpt4 access), sentence_transformers (for lightweight sentence embedding), and pinecone (cloud vector database) to create a free-to-use version of BabyAGI. If good response, will try making free BabyCoder.

Current Major Issues:
- No Stop Condition
- No way to conglomerate results from previous tasks (n=1 rn)

Current improvements over vanilla BabyAGI:
- Implemented long-term memory for BabyAGI (feeds the execution agent the results and task name of an already completed task that is most relevant to the current one) — works pretty well
- Modified task generator to ensure that tasks are executable by an LLM
- Modified long-term memory storage to embed vectors by task-name rather than task result—makes relevant result retrieval more accurate
