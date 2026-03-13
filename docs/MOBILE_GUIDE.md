# Mobile Guide — ACE Framework on a-Shell / a-Shell mini

This guide covers running ACE Framework directly on your iPhone using
[a-Shell](https://holzschu.github.io/a-Shell_iOS/) or
[a-Shell mini](https://apps.apple.com/app/a-shell-mini/id1543537943).

## Prerequisites

- a-Shell or a-Shell mini installed on your iPhone
- Internet connection (only needed for initial setup)

## Step 1 — Install Python packages

Open a-Shell and run:

```sh
pip install pytest
```

That's all you need. The framework uses Python stdlib only for core functionality.

## Step 2 — Get the project

### Option A: Clone with git (if available)

```sh
git clone https://github.com/PhungKhacVu/ACE-Famework.git
cd ACE-Famework
```

### Option B: Download ZIP

1. Visit https://github.com/PhungKhacVu/ACE-Famework in Safari
2. Tap **Code → Download ZIP**
3. Extract to your Files app
4. In a-Shell: `cd ~/Documents/ACE-Famework-main`

## Step 3 — Verify the setup

```sh
python -m pytest tests/ -v
```

You should see 51 tests passing.

## Step 4 — Run your first task

```sh
python -m app.cli show-playbook
python -m app.cli run-task --input data/sample_tasks.json --no-adapt
```

## Step 5 — Run the full adaptation loop

```sh
python -m app.cli adapt --input data/sample_tasks.json
```

## Tips for a-Shell

### Screen width
If output is cut off, increase the font size or rotate to landscape:

```sh
# Show playbook with fewer bullets
python -m app.cli show-playbook --limit 5
```

### Save results to file

```sh
python -m app.cli run-task --input data/sample_tasks.json \
  --output ~/Documents/results.json --no-adapt
```

### Add your own tasks

Create a JSON file:

```sh
cat > ~/Documents/my_tasks.json << 'EOF'
[
  {
    "id": "my-task-1",
    "instruction": "What is the capital of Vietnam?",
    "domain": "general",
    "ground_truth": "Hanoi"
  }
]
EOF
python -m app.cli adapt --input ~/Documents/my_tasks.json
```

### View the playbook as plain text

```sh
cat data/playbook.json
```

### Reset the playbook to starter bullets

```sh
git checkout data/playbook.json
```

## Using a Local LLM with Ollama (Advanced)

If you have a Mac/PC running Ollama on the same Wi-Fi network:

```sh
# On your Mac/PC
ollama serve  # starts on port 11434

# In a-Shell (set the IP of your Mac/PC)
export ACE_LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://192.168.1.x:11434
export OLLAMA_MODEL=llama3

python -m app.cli adapt --input data/sample_tasks.json \
  --provider ollama
```

## File Layout (on-device)

```
ACE-Famework/
├── app/          ← Python source code
├── data/
│   ├── playbook.json        ← your growing playbook (edit freely)
│   └── sample_tasks.json    ← example tasks
├── tests/        ← run with: python -m pytest tests/
└── docs/         ← documentation
```

## Performance Notes

- The mock provider is instant (no network, no GPU)
- Tests run in < 2 seconds on iPhone
- The playbook JSON is small and loads instantly
- Deduplication uses pure Python — no numpy needed
