/* Drag and Drop event handlers

Copyright (c) 2024-present Hannah Esther Augustijn, MSc

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

function handleDrag(event) {}

function handleDragStart(event) {
    var dragged = event.target;
    event.target.style.opacity = .5;
    event.dataTransfer.setData("draggedAccId", event.target.id);
    setTimeout(() => event.target.classList.toggle("hidden"));
    if (event.target.classList.contains("dropzone")) {
        event.target.style.background = "#a3a3a3";
    }
    document.querySelectorAll('.dropzone').forEach(function(dropzone) {
        dropzone.classList.add('dropzone-dragging');
    });
}

function handleDragEnd(event) {
    event.target.style.opacity = "";
    document.querySelectorAll('.dropzone').forEach(function(dropzone) {
        dropzone.classList.remove('dropzone-dragging');
    });
}

function handleDragOver(event) {
    event.preventDefault();
}

function handleDragEnter(event) {
    if (event.target.classList.contains("dropzone")) {
        event.target.style.background = "#a3a3a3";
    }
}

function handleDragLeave(event) {
    if (event.target.classList.contains("dropzone")) {
        event.target.style.background = "";
    }
}

function handleDrop(event) {
    event.preventDefault();
    if (event.target.classList.contains("dropzone")) {
        event.target.style.background = "";
        const draggedAccId = event.dataTransfer.getData("draggedAccId");
        const draggedAcc = document.getElementById(draggedAccId);
        const fromContainer = draggedAcc.parentNode;
        const toContainer = event.target;
        if (toContainer !== fromContainer) {
            const existingAcc = toContainer.firstElementChild;
            if (existingAcc) {
                fromContainer.appendChild(existingAcc);
            }
            toContainer.appendChild(draggedAcc);
        } else {
            toContainer.appendChild(draggedAcc);
        }

        setTimeout(() => {
            document.querySelectorAll('.js-plotly-plot').forEach(el => {
                Plotly.Plots.resize(el);
            });
        }, 50);
    }
}

// Function to add event listeners
export function enableDragAndDrop() {
    document.querySelectorAll('.accordion').forEach(function(item) {
        item.setAttribute('draggable', 'true');
    });
    document.addEventListener("drag", handleDrag, false);
    document.addEventListener("dragstart", handleDragStart, false);
    document.addEventListener("dragend", handleDragEnd, false);
    document.addEventListener("dragover", handleDragOver, false);
    document.addEventListener("dragenter", handleDragEnter, false);
    document.addEventListener("dragleave", handleDragLeave, false);
    document.addEventListener("drop", handleDrop, false);
}

// Function to remove event listeners
export function disableDragAndDrop() {
    document.querySelectorAll('.accordion').forEach(function(item) {
        item.removeAttribute('draggable');
    });
    document.removeEventListener("drag", handleDrag, false);
    document.removeEventListener("dragstart", handleDragStart, false);
    document.removeEventListener("dragend", handleDragEnd, false);
    document.removeEventListener("dragover", handleDragOver, false);
    document.removeEventListener("dragenter", handleDragEnter, false);
    document.removeEventListener("dragleave", handleDragLeave, false);
    document.removeEventListener("drop", handleDrop, false);
}