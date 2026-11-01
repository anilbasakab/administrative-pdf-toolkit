// Reorder Pages: drag pictures of the pages, or use the arrow buttons,
// which also work on phones and with a keyboard.
export default function ({ data, parentElement, setStateValue }) {
    let grid = parentElement.querySelector(".reorder-grid");

    // Streamlit calls this on every page refresh: keep what the user arranged
    if (grid && grid.dataset.signature === data.signature) {
        return;
    }

    if (grid) {
        grid.remove();
    }

    grid = document.createElement("div");
    grid.className = "thumb-grid reorder-grid";
    grid.dataset.signature = data.signature;

    const refreshNumbers = () => {
        [...grid.children].forEach((item, position) => {
            item.querySelector(".reorder-position").textContent = position + 1;
        });
    };

    const saveOrder = () => {
        refreshNumbers();
        setStateValue(
            "order",
            [...grid.children].map((item) => Number(item.dataset.page))
        );
    };

    let dragged = null;

    const makeButton = (label, title, move) => {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = label;
        button.title = title;
        button.setAttribute("aria-label", title);
        button.addEventListener("click", () => {
            move();
            saveOrder();
            button.focus();
        });
        return button;
    };

    data.order.forEach((pageIndex) => {
        const item = document.createElement("figure");
        item.className = "thumb reorder-item";
        item.draggable = true;
        item.dataset.page = pageIndex;

        const position = document.createElement("span");
        position.className = "reorder-position";

        const image = document.createElement("img");
        image.src = `data:image/jpeg;base64,${data.thumbnails[pageIndex]}`;
        image.alt = "";
        image.draggable = false;

        const caption = document.createElement("figcaption");
        caption.textContent = `Page ${pageIndex + 1}`;

        const buttons = document.createElement("div");
        buttons.className = "reorder-buttons";
        buttons.append(
            makeButton("←", `Move page ${pageIndex + 1} earlier`, () => {
                if (item.previousElementSibling) {
                    grid.insertBefore(item, item.previousElementSibling);
                }
            }),
            makeButton("→", `Move page ${pageIndex + 1} later`, () => {
                if (item.nextElementSibling) {
                    grid.insertBefore(item.nextElementSibling, item);
                }
            })
        );

        item.append(position, image, caption, buttons);

        item.addEventListener("dragstart", (event) => {
            dragged = item;
            event.dataTransfer.effectAllowed = "move";
            event.dataTransfer.setData("text/plain", String(pageIndex));
            item.classList.add("reorder-dragging");
        });

        item.addEventListener("dragover", (event) => {
            event.preventDefault();

            if (!dragged || dragged === item) {
                return;
            }

            const box = item.getBoundingClientRect();
            const after = event.clientX > box.left + box.width / 2;
            grid.insertBefore(dragged, after ? item.nextElementSibling : item);
        });

        item.addEventListener("drop", (event) => event.preventDefault());

        item.addEventListener("dragend", () => {
            item.classList.remove("reorder-dragging");
            dragged = null;
            saveOrder();
        });

        grid.append(item);
    });

    refreshNumbers();
    parentElement.append(grid);
}
