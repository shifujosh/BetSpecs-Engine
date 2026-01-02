# BetSpecs: Deterministic RAG & Real-Time Ingestion

> **Note:** Source code is proprietary. This repository demonstrates the verification architecture.

BetSpecs is a real-time analytics engine that solves the "hallucination problem" in LLMs when dealing with numerical sports data. It operates as a specialized **Swarm Agent** within the **[JACQ Ecosystem](https://github.com/shifujosh/JACQ-Architecture)**.

It introduces a **Verification Layer**—inspired by high-frequency trading pipelines (see [Market-Data-Pipeline-Ref](https://github.com/shifujosh/Market-Data-Pipeline-Ref-))—that forces LLM outputs to pass a deterministic truth check against raw SQL data.

## The Verification Flow

```mermaid
flowchart LR
    %% --- Styling (Dark Mode Native) ---
    classDef stream fill:#1e293b,stroke:#3b82f6,stroke-width:1px,color:#93c5fd;
    classDef db fill:#1e293b,stroke:#0ea5e9,stroke-width:2px,color:#7dd3fc;
    classDef logic fill:#1e293b,stroke:#a855f7,stroke-width:2px,color:#d8b4fe;
    classDef error fill:#2a1a1a,stroke:#ef4444,stroke-width:2px,color:#fca5a5;
    classDef success fill:#1e293b,stroke:#10b981,stroke-width:2px,color:#6ee7b7;

    Stream[Real-Time Data Stream]:::stream -->|Ingest| Norm[Normalized Schema]:::db
    Norm -.->|See Bloomberg Pipeline Ref| DB[(SQL Ground Truth)]:::db
    
    User[User Query] -->|Intent| LLM[LLM Inference]:::stream
    LLM -->|Retrieval| DB
    
    subgraph "Trust Layer (Data Physics)"
        LLM -->|Draft Output| Verifier[Verification Agent]:::logic
        DB -->|Cross-Reference| Verifier
        Verifier -->|Pass| Final[Client UI]:::success
        Verifier -.->|Fail| Error[Reject & Regenerate]:::error
    end
```

## Key Innovations

### 1. Vector Anchors
We do not feed raw stats to the LLM context blindly. We use "Anchor Embeddings" to retrieve only the relevant game state rows, reducing context window noise.

### 2. Deterministic Logic Gates
The **Verification Agent** is not an LLM. It is a logic engine that parses the LLM's JSON output and queries the SQL database directly. 
- If `LLM says "Player scored 30"` AND `DB says "Player scored 20"` -> **REJECT & REGENERATE**.

### 3. Real-Time Ingestion
Data is normalized from multiple firehose providers (Sportradar, Genius) and normalized into a unified schema within sub-milliseconds.
