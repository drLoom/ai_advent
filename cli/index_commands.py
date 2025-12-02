"""CLI commands for document indexing."""
from typing import Optional
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from indexing.index_manager import IndexManager
from indexing.reranker import Reranker
from ai.open_ai_client import OpenAIClient


app = typer.Typer(help="Document indexing commands")
console = Console()


def get_index_manager() -> IndexManager:
    """Get or create index manager instance."""
    return IndexManager()


@app.command()
def add(
    path: str = typer.Argument(
        ...,
        help="Path to file or directory to index"
    ),
    recursive: bool = typer.Option(
        True,
        "--recursive/--no-recursive",
        "-r",
        help="Search directories recursively"
    ),
    file_types: Optional[str] = typer.Option(
        None,
        "--file-types",
        "-t",
        help="Comma-separated list of file extensions (e.g., pdf,md,py)"
    ),
    chunk_size: int = typer.Option(
        500,
        "--chunk-size",
        "-c",
        help="Chunk size in tokens"
    ),
    chunk_overlap: int = typer.Option(
        50,
        "--chunk-overlap",
        "-o",
        help="Overlap between chunks in tokens"
    )
):
    """Add documents to the index from a file or directory."""
    try:
        manager = IndexManager(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        file_path = Path(path)

        if file_path.is_file():
            console.print(f"[cyan]Indexing file:[/cyan] {path}")
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Processing...", total=None)
                doc_id = manager.index_document(str(file_path))
                progress.update(task, completed=True)

            if doc_id:
                console.print(
                    f"[green]✓[/green] Successfully indexed "
                    f"document (ID: {doc_id})"
                )
            else:
                console.print("[yellow]No content indexed[/yellow]")

        elif file_path.is_dir():
            file_type_list = None
            if file_types:
                file_type_list = [
                    ft.strip() for ft in file_types.split(',')
                ]

            console.print(
                f"[cyan]Indexing directory:[/cyan] {path}"
            )
            if file_type_list:
                console.print(
                    f"[cyan]File types:[/cyan] {', '.join(file_type_list)}"
                )

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Indexing documents...", total=None)
                doc_ids = manager.index_directory(
                    str(file_path),
                    recursive=recursive,
                    file_types=file_type_list
                )
                progress.update(task, completed=True)

            console.print(
                f"[green]✓[/green] Indexed {len(doc_ids)} documents"
            )

        else:
            console.print(f"[red]Error:[/red] Path not found: {path}")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    top_k: int = typer.Option(
        5,
        "--top-k",
        "-k",
        help="Number of results to return"
    )
):
    """Search indexed documents."""
    try:
        manager = get_index_manager()

        console.print(f"[cyan]Searching for:[/cyan] {query}\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Searching...", total=None)
            results = manager.search(query, top_k=top_k)
            progress.update(task, completed=True)

        if not results:
            console.print("[yellow]No results found[/yellow]")
            return

        console.print(f"\n[green]Found {len(results)} results:[/green]\n")

        for i, (metadata, score) in enumerate(results, 1):
            title = metadata.get('title')
            console.print(f"[bold cyan]{i}. {title}[/bold cyan]")
            console.print(f"   Score: {score:.4f}")
            console.print(f"   File: {metadata.get('file_path')}")

            # Show section title if available (markdown)
            section_title = metadata.get('section_title')
            if section_title:
                console.print(f"   Section: {section_title}")

            # Show page number if available (PDF)
            page_num = metadata.get('page_number')
            if page_num:
                console.print(f"   Page: {page_num}")

            console.print(f"   Chunk: {metadata.get('chunk_index')}")
            preview = metadata.get('content', '')[:150]
            console.print(f"   Preview: {preview}...")
            console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask"),
    top_k: int = typer.Option(
        5,
        "--top-k",
        "-k",
        help="Number of context chunks to retrieve"
    ),
    model: str = typer.Option(
        "google/gemini-2.5-flash-lite-preview-09-2025",
        "--model",
        "-m",
        help="LLM model to use"
    ),
    show_sources: bool = typer.Option(
        True,
        "--show-sources/--no-sources",
        help="Show source documents"
    ),
    rerank: bool = typer.Option(
        False,
        "--rerank/--no-rerank",
        help="Use reranking to improve result quality"
    ),
    rerank_model: str = typer.Option(
        "deepseek/deepseek-v3.2-speciale",
        "--rerank-model",
        help="Model to use for reranking"
    ),
    relevance_threshold: float = typer.Option(
        0.5,
        "--threshold",
        "-t",
        help="Minimum relevance score (0-1) for reranking"
    )
):
    """Ask a question using RAG (Retrieval-Augmented Generation)."""
    try:
        manager = get_index_manager()

        console.print(f"[cyan]Question:[/cyan] {question}\n")

        # Step 1: Search for relevant chunks
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Searching documents...", total=None)
            initial_results = manager.search(
                question,
                top_k=top_k * 2 if rerank else top_k
            )
            progress.update(task, completed=True)

        if not initial_results:
            console.print(
                "[yellow]No relevant documents found. "
                "Please index some documents first.[/yellow]"
            )
            return

        # Step 1.5: Rerank results if requested
        if rerank:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Reranking results...", total=None)
                reranker = Reranker(
                    model=rerank_model,
                    threshold=relevance_threshold
                )
                reranked = reranker.rerank(
                    question,
                    initial_results,
                    top_k=top_k
                )
                progress.update(task, completed=True)

            if not reranked:
                console.print(
                    "[yellow]No results passed relevance threshold "
                    f"({relevance_threshold}). "
                    "Try lowering --threshold.[/yellow]"
                )
                return

            # Convert reranked results back to (metadata, score) format
            # Store relevance scores for display
            results = [
                (metadata, similarity)
                for metadata, similarity, relevance in reranked
            ]
            relevance_scores = [
                relevance for _, _, relevance in reranked
            ]

            console.print(
                f"[dim]Filtered {len(initial_results)} → "
                f"{len(results)} results "
                f"(threshold: {relevance_threshold})[/dim]\n"
            )
        else:
            results = initial_results
            relevance_scores = None

        # Step 2: Format context from retrieved chunks
        context_parts = []
        sources = []

        for i, (metadata, score) in enumerate(results, 1):
            content = metadata.get('content', '')
            title = metadata.get('title', 'Unknown')
            file_path = metadata.get('file_path', 'Unknown')
            page_num = metadata.get('page_number')
            section_title = metadata.get('section_title')

            context_parts.append(
                f"[Document {i}: {title}]\n{content}\n"
            )

            source = {
                'title': title,
                'file': file_path,
                'score': score,
                'page': page_num,
                'section': section_title
            }

            # Add relevance score if reranking was used
            if relevance_scores:
                source['relevance'] = relevance_scores[i - 1]

            sources.append(source)

        context = "\n".join(context_parts)

        # Step 3: Create prompt for LLM
        system_prompt = """You are a helpful assistant that answers questions based on provided document context.

Guidelines:
- Answer based ONLY on the information in the provided documents
- If the answer is not in the documents, say "I don't have enough information to answer that question."
- Be concise and direct
- Cite specific details from the documents when relevant
- If documents conflict, mention the different perspectives"""

        user_prompt = f"""Context from indexed documents:

{context}

---

Question: {question}

Please provide a clear and concise answer based on the context above."""

        # Step 4: Call LLM
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating answer...", total=None)

            client = OpenAIClient.new()
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )

            progress.update(task, completed=True)

        # Step 5: Display answer
        answer = response.choices[0].message.content

        console.print("\n[bold green]Answer:[/bold green]\n")
        console.print(answer)
        console.print()

        # Step 6: Show sources if requested
        if show_sources:
            console.print("\n[bold cyan]Sources:[/bold cyan]\n")
            for i, source in enumerate(sources, 1):
                # Build location info (section or page)
                location_parts = []
                if source.get('section'):
                    location_parts.append(f"Section: {source['section']}")
                if source.get('page'):
                    location_parts.append(f"Page {source['page']}")

                location_info = (
                    f" ({', '.join(location_parts)})"
                    if location_parts else ""
                )

                # Build score info
                similarity = source['score']
                score_info = f"similarity: {similarity:.2f}"

                # Add relevance score if available
                if source.get('relevance') is not None:
                    relevance = source['relevance']
                    score_info += f", relevance: {relevance:.2f}"

                console.print(
                    f"{i}. {source['title']}{location_info} "
                    f"({score_info})"
                )
                console.print(f"   File: {source['file']}")
            console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def list_docs(
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum number of documents to show"
    )
):
    """List all indexed documents."""
    try:
        manager = get_index_manager()
        docs = manager.list_documents(limit=limit)

        if not docs:
            console.print("[yellow]No documents indexed yet[/yellow]")
            return

        table = Table(title="Indexed Documents")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="green")
        table.add_column("Type", style="blue")
        table.add_column("Path", style="white")
        table.add_column("Indexed At", style="yellow")

        for doc in docs:
            table.add_row(
                str(doc['id']),
                doc.get('title', 'N/A')[:50],
                doc.get('file_type', 'N/A'),
                str(Path(doc['file_path']).name),
                doc.get('indexed_at', 'N/A')[:19]
            )

        console.print(table)
        console.print(f"\n[cyan]Total:[/cyan] {len(docs)} documents")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def stats():
    """Show indexing statistics."""
    try:
        manager = get_index_manager()
        stats = manager.get_stats()

        table = Table(title="Index Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Documents", str(stats['total_documents']))
        table.add_row("Total Chunks", str(stats['total_chunks']))
        table.add_row(
            "Vector Store Size",
            f"{stats['vector_store']['total_vectors']} vectors"
        )
        table.add_row(
            "Embedding Dimension",
            str(stats['vector_store']['dimension'])
        )

        db_size_mb = stats['database_size_bytes'] / (1024 * 1024)
        table.add_row("Database Size", f"{db_size_mb:.2f} MB")

        index_size_mb = (
            stats['vector_store']['index_size_bytes'] / (1024 * 1024)
        )
        table.add_row("Index Size", f"{index_size_mb:.2f} MB")

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def delete(
    doc_id: int = typer.Argument(..., help="Document ID to delete")
):
    """Delete a document from the index."""
    try:
        confirm = typer.confirm(
            f"Are you sure you want to delete document {doc_id}?"
        )
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

        manager = get_index_manager()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Deleting...", total=None)
            success = manager.delete_document(doc_id)
            progress.update(task, completed=True)

        if success:
            console.print(
                f"[green]✓[/green] Deleted document {doc_id}"
            )
        else:
            console.print(f"[yellow]Document {doc_id} not found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def ranking(
    question: str = typer.Argument(..., help="Question to compare"),
    top_k: int = typer.Option(
        5,
        "--top-k",
        "-k",
        help="Number of results to compare"
    ),
    rerank_model: str = typer.Option(
        "deepseek/deepseek-v3.2-speciale",
        "--rerank-model",
        help="Model to use for reranking"
    ),
    threshold: float = typer.Option(
        0.5,
        "--threshold",
        "-t",
        help="Minimum relevance score (0-1)"
    )
):
    """Compare search results with and without reranking."""
    try:
        manager = get_index_manager()

        console.print(
            f"[cyan]Comparing results for:[/cyan] {question}\n"
        )

        # Step 1: Get initial search results
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Searching...", total=None)
            initial_results = manager.search(question, top_k=top_k * 2)
            progress.update(task, completed=True)

        if not initial_results:
            console.print("[yellow]No results found[/yellow]")
            return

        # Step 2: Rerank results
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Reranking...", total=None)
            reranker = Reranker(model=rerank_model, threshold=threshold)
            reranked = reranker.rerank(
                question,
                initial_results,
                top_k=top_k
            )
            progress.update(task, completed=True)

        # Step 3: Display comparison
        console.print(
            f"[bold]Initial Results (top {top_k}):[/bold]\n"
        )

        for i, (metadata, sim_score) in enumerate(
            initial_results[:top_k], 1
        ):
            title = metadata.get('title', 'Unknown')
            section = metadata.get('section_title', '')
            page = metadata.get('page_number')

            location = f" - {section}" if section else ""
            location += f" (Page {page})" if page else ""

            console.print(
                f"{i}. [cyan]{title}{location}[/cyan]"
            )
            console.print(f"   Similarity: {sim_score:.3f}")

        console.print(
            f"\n[bold]After Reranking "
            f"(threshold={threshold}):[/bold]\n"
        )

        if not reranked:
            console.print(
                f"[yellow]No results passed threshold "
                f"of {threshold}[/yellow]"
            )
        else:
            for i, (metadata, sim_score, rel_score) in enumerate(
                reranked, 1
            ):
                title = metadata.get('title', 'Unknown')
                section = metadata.get('section_title', '')
                page = metadata.get('page_number')

                location = f" - {section}" if section else ""
                location += f" (Page {page})" if page else ""

                # Highlight high relevance
                rel_color = (
                    "green" if rel_score >= 0.7
                    else "yellow" if rel_score >= 0.5
                    else "red"
                )

                console.print(
                    f"{i}. [cyan]{title}{location}[/cyan]"
                )
                console.print(
                    f"   Similarity: {sim_score:.3f}, "
                    f"Relevance: [{rel_color}]{rel_score:.3f}[/{rel_color}]"
                )

        # Step 4: Summary
        console.print(
            f"\n[bold]Summary:[/bold]\n"
            f"  Initial results: {len(initial_results)}\n"
            f"  After filtering: {len(reranked)}\n"
            f"  Filtered out: "
            f"{len(initial_results[:top_k * 2]) - len(reranked)}"
        )

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def reindex(
    doc_id: Optional[int] = typer.Option(
        None,
        "--doc-id",
        "-d",
        help="Specific document ID to reindex (omit to reindex all)"
    ),
    all_docs: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Reindex all documents"
    )
):
    """Reindex documents."""
    try:
        manager = get_index_manager()

        if all_docs:
            confirm = typer.confirm(
                "This will reindex all documents. Continue?"
            )
            if not confirm:
                console.print("[yellow]Cancelled[/yellow]")
                return

            console.print("[cyan]Reindexing all documents...[/cyan]")
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Reindexing...", total=None)
                manager.reindex_all()
                progress.update(task, completed=True)

            console.print("[green]✓[/green] Reindexing complete")

        elif doc_id is not None:
            console.print(f"[cyan]Reindexing document {doc_id}...[/cyan]")
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Reindexing...", total=None)
                success = manager.reindex_document(doc_id)
                progress.update(task, completed=True)

            if success:
                console.print(
                    f"[green]✓[/green] Reindexed document {doc_id}"
                )
            else:
                console.print(
                    f"[yellow]Document {doc_id} not found[/yellow]"
                )

        else:
            console.print(
                "[yellow]Please specify --doc-id or --all[/yellow]"
            )

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)
