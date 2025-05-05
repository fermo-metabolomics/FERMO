/* Handles the dynamic loading of dashboard tables

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

import { visualizeData, addBoxVisualization } from './chromatogram.js';
import { visualizeNetwork } from './network.js'

// Functions to dynamically update tables after feature or sample selection //
export function updateFeatureTables(featureId, sampleData, filteredSampleData) {
    for (var i = 0; i < sampleData.featureId.length; i++) {
        if (sampleData.featureId[i] == featureId) {
            showTables()
            document.getElementById('activeFeature').textContent =
            'Network visualization of feature: ' + featureId;
            const networkType = document.getElementById('networkSelect').value;
            visualizeData(filteredSampleData, networkType, true, 0, 1);
            addBoxVisualization(sampleData.traceInt[i], sampleData.traceRt[i]);
            updateTableWithFeatureData(i, sampleData, networkType);
            updateTableWithGroupData(sampleData.fGroupData[i]);
            updateTableWithSampleData(sampleData.fSampleData[i], sampleData.aSampleData[i]);
            updateTableWithAnnotationData(sampleData.annotations[i]);
            return i;
            break;
        }
    }
}

function updateTableWithFeatureData(fId, sampleData, networkType) {
    document.getElementById('featureIdCell').textContent = sampleData.featureId[fId];
    document.getElementById('precMzCell').textContent = sampleData.precMz[fId];
    document.getElementById('retTimeCell').textContent = sampleData.retTime[fId];
    document.getElementById('relIntCell').textContent = sampleData.relInt[fId];
    document.getElementById('absIntCell').textContent = sampleData.absInt[fId];
    document.getElementById('NovScore').textContent = sampleData.novScore[fId];
    document.getElementById('BlankAs').textContent = sampleData.blankAs[fId]
    const networkId = networkType === 'modified_cosine' ? sampleData.idNetCos[fId] : sampleData.idNetMs[fId];
    document.getElementById('NetworkId').textContent = networkId;
}


function updateTableWithGroupData(groupData){
    var featureData = Object.entries(groupData);
    if (Object.keys(featureData).length === 0) {
        document.getElementById('feature-general-info').textContent = 'No group data available for this feature.'
        clearHeatmaps();
    } else {
        document.getElementById('feature-general-info').textContent = 'The feature is found in the following groups:'
        for (const [key, value] of featureData) {
            createHeatmap(value, key);
        }
    }
}

function updateTableWithSampleData(sampleIntensity, sampleArea) {
    let tableBody = document.getElementById("sampleCell");
    tableBody.innerHTML = "";

    // Create maps for quick lookup by s_id
    let intensityMap = new Map();
    sampleIntensity.forEach(item => {
        intensityMap.set(item.s_id, item.value);
    });

    let areaMap = new Map();
    sampleArea.forEach(item => {
        areaMap.set(item.s_id, item.value);
    });

    // Iterate over the sampleIntensity array and match with sampleArea
    sampleIntensity.forEach(intensityItem => {
        let s_id = intensityItem.s_id;
        if (areaMap.has(s_id)) {
            let row = document.createElement("tr");

            // Sample Intensity Data
            let sIdIntensityCell = document.createElement("td");
            sIdIntensityCell.textContent = s_id;
            row.appendChild(sIdIntensityCell);

            let valueIntensityCell = document.createElement("td");
            valueIntensityCell.textContent = intensityItem.value;
            row.appendChild(valueIntensityCell);

            // Sample Area Data
            let valueAreaCell = document.createElement("td");
            valueAreaCell.textContent = areaMap.get(s_id);
            row.appendChild(valueAreaCell);

            tableBody.appendChild(row);
        }
    });
}

function updateTableWithAnnotationData(annotations, sample) {
    // Check if annotations is empty
    if (Object.keys(annotations).length === 0) {
        let annMessage = document.getElementById("feature-annotation");
        annMessage.innerHTML = "No annotation data found for this feature.";
        document.getElementById('matchTable').style.display = 'none';
        document.getElementById('phenotypeTable').style.display = 'none';
        document.getElementById('adductTable').style.display = 'none';
        document.getElementById('fragmentTable').style.display = 'none';
        document.getElementById('lossesTable').style.display = 'none';
        return;
    }

    // Define headers and columns for each section
    let matchHeaders = ["Match id", "Score", "More info"];
    let matchColumns = ["id", "score"];
    let matchExtraColumns = [
        { title: "Algorithm", field: "algorithm" },
        { title: "Library", field: "library" },
        { title: "Mz", field: "mz" },
        { title: "Difference in mz", field: "diff_mz" },
        { title: "SMILES", field: "smiles" },
        { title: "Link to MIBiG", field: "id" }
    ];

    let phenoHeaders = ["Phenotype description", "Score", "More info"];
    let phenoColumns = ["descr", "score"];
    let phenoExtraColumns = [
        { title: "Format", field: "format" },
        { title: "Category", field: "category" },
        { title: "P value", field: "p_value" },
        { title: "Corrected p value", field: "p_value_corr" }
    ];

    let lossHeaders = ["Loss id", "Difference in ppm", "More info"];
    let lossColumns = ["id", "diff_ppm"];
    let lossExtraColumns = [
        { title: "Detected loss", field: "det_loss" },
        { title: "Expected loss", field: "exp_loss" },
        { title: "Fragment mz", field: "mz_frag" }
    ];

    let fragmentHeaders = ["Fragment id", "Difference in ppm", "More info"];
    let fragmentColumns = ["id", "diff_ppm"];
    let fragmentExtraColumns = [
        { title: "Detected fragment", field: "frag_det" },
        { title: "Expected fragment", field: "frag_ex" }
    ];

    let adductHeaders = ["Adduct type", "Difference in ppm", "More info"];
    let adductColumns = ["adduct_type", "diff_ppm"];
    let adductExtraColumns = [
        { title: "Partner adduct", field: "partner_adduct" },
        { title: "Partner mz", field: "partner_mz" },
        { title: "Partner id", field: "partner_id" },
        { title: "difference in ppm", field: "diff_ppm" }
    ];


    createAnnotationTable("matchTable", annotations.matches, matchHeaders, matchColumns, matchExtraColumns, "match");
    createAnnotationTable("phenotypeTable", annotations.phenotypes, phenoHeaders, phenoColumns, phenoExtraColumns, "phenotype");
    createAnnotationTable("lossesTable", annotations.losses, lossHeaders, lossColumns, lossExtraColumns, "loss");
    createAnnotationTable("fragmentTable", annotations.fragments, fragmentHeaders, fragmentColumns, fragmentExtraColumns, "fragment");
    createAnnotationTable("adductTable", annotations.adducts, adductHeaders, adductColumns, adductExtraColumns, "adduct");
}

function createAnnotationTable(sectionId, annotations, headers, columns, extraColumns, tableId) {
    let tableBody = document.getElementById(sectionId);
    tableBody.innerHTML = "";

    let annMessage = document.getElementById("feature-annotation");
    annMessage.innerHTML = "";

    if (annotations.length > 0) {
        let tHead = createTableHeader(headers);
        tableBody.appendChild(tHead);

        let tBody = createTableBody(annotations, columns, extraColumns, tableId);
        tableBody.appendChild(tBody);

        tableBody.style.marginBottom = "1rem";
        return true;
    } else {
        tableBody.style.marginBottom = "0";
        return false;
    }
}

function createTableHeader(headers) {
    let tHead = document.createElement("thead");
    let rowHead = document.createElement("tr");

    headers.forEach((header, index) => {
        let th = document.createElement("th");
        th.textContent = header;
        if (index === headers.length - 1) {
            th.className = "text-center";
        }
        rowHead.appendChild(th);
    });

    tHead.appendChild(rowHead);
    return tHead;
}

function createTableRow(data, columns, rowId, tableId) {
    let row = document.createElement("tr");

    columns.forEach(column => {
        let td = document.createElement("td");
        td.className = "custom-row-padding";
        let cellData = data[column];
        if (typeof cellData === 'string' && cellData.includes("|")) {
            td.textContent = cellData.split("|")[0];
        } else {
            td.textContent = cellData !== undefined ? cellData : '';
        }
        row.appendChild(td);
    });

    // Add the collapse button for expanding extra info
    let expandCell = document.createElement("td");
    expandCell.className = "text-center custom-row-padding";
    let expandButton = document.createElement("button");
    expandButton.className = "accordion-button-info collapsed";
    expandButton.type = "button";
    expandButton.setAttribute("data-bs-toggle", "collapse");
    expandButton.setAttribute("data-bs-target", `#collapse-${tableId}-${rowId}`);
    expandButton.setAttribute("aria-expanded", "false");
    expandButton.setAttribute("aria-controls", `collapse-${tableId}-${rowId}`);

    expandCell.appendChild(expandButton);
    row.appendChild(expandCell);

    return row;
}

function createTableBody(dataArray, columns, extraColumns, tableId) {
    let tBody = document.createElement("tbody");

    dataArray.forEach((data, index) => {
        let row = createTableRow(data, columns, index, tableId);
        tBody.appendChild(row);

        // Create the extra info row
        let extraInfoRow = document.createElement("tr");
        let extraInfoCell = document.createElement("td");
        extraInfoCell.colSpan = columns.length + 1;
        extraInfoCell.style.padding = "0px";

        let collapseDiv = document.createElement("div");
        collapseDiv.id = `collapse-${tableId}-${index}`;
        collapseDiv.className = "collapse";

        let { extraInfo } = createExtraInfoRow(data, extraColumns, columns.length + 1);
        collapseDiv.appendChild(extraInfo);

        extraInfoCell.appendChild(collapseDiv);
        extraInfoRow.appendChild(extraInfoCell);

        tBody.appendChild(extraInfoRow);
    });

    return tBody;
}

function clickToCopy(data, displayText) {
    const span = document.createElement("span");
    span.textContent = displayText;
    span.style.cursor = "pointer";
    span.style.color = "rgba(13, 110, 253)";

    span.onclick = function() {
        const tempInput = document.createElement("input");
        tempInput.value = data;
        document.body.appendChild(tempInput);
        tempInput.select();
        document.execCommand("copy");
        document.body.removeChild(tempInput);

        alert("Copied to clipboard: \n" + data);
    };

    return span;
}

function createExtraInfoRow(data, extraColumns, colspan) {
    let extraInfo = document.createElement("div");
    extraInfo.style.padding = "10px";
    extraInfo.style.backgroundColor = "#f9f9f9";
    extraInfo.style.fontSize = "0.8em";

    let infoTable = document.createElement("table");
    infoTable.classList.add("fixed-width-table-extra");

    extraColumns.forEach(column => {
        let cellData = data[column.field];
        let infoRow = document.createElement("tr");

        let titleCell = document.createElement("td");
        titleCell.textContent = column.title + ":";
        titleCell.style.fontWeight = "bold";
        infoRow.appendChild(titleCell);

        let valueCell = document.createElement("td");
        if (column.title === "Link to MIBiG") {
            if (typeof cellData === 'string' && cellData.includes("|")) {
                let mibigLink = document.createElement('a');
                mibigLink.href = `https://bioregistry.io/mibig:${cellData.split("|")[1]}`;
                mibigLink.textContent = cellData.split("|")[1];
                mibigLink.target = "_blank";
                valueCell.appendChild(mibigLink);
            } else {
                return;
            }
        } else {
            valueCell.textContent = cellData !== undefined ? cellData : '';
        }

        if (column.title === "SMILES") {
            let displayText = "Copy SMILES";
            let copySpan = clickToCopy(cellData, displayText);
            valueCell.innerHTML = '';
            valueCell.appendChild(copySpan);
        }

        infoRow.appendChild(valueCell);
        infoTable.appendChild(infoRow);
    });

    extraInfo.appendChild(infoTable);

    return { extraInfo };
}

// Heatmap visualization function //
function createHeatmap(data, groupName) {
    const groupValues = [...new Set([...data.map(item => item.group1), ...data.map(item => item.group2)])].sort();
    const matrix = groupValues.map(() => Array(groupValues.length).fill(0));

    // Fill the matrix with factor values
    data.forEach(item => {
        const rowIndex = groupValues.indexOf(item.group1);
        const colIndex = groupValues.indexOf(item.group2);
        matrix[rowIndex][colIndex] = item.factor;
        matrix[colIndex][rowIndex] = item.factor;
    });
    const reversedMatrix = matrix.reverse();
    const reversedGroupValues = [...groupValues].reverse();

    // Create value annotations to be shown within the heatmap
    const annotations = [];
    for (let i = 0; i < reversedGroupValues.length; i++) {
        for (let j = 0; j < groupValues.length; j++) {
            if (reversedMatrix[i][j] !== null) {
                annotations.push({
                    x: groupValues[j],
                    y: reversedGroupValues[i],
                    text: reversedMatrix[i][j].toFixed(2),
                    showarrow: false,
                    font: { size: 7 }
                });
            }
        }
    }

    // Define colorscale
    const colorscaleValue = [
        [0, '#f5f5f5'],
        [0.01, '#dbf3ff'],
        [1, '#de4b4b']
    ];

    // Create a new Plotly figure
    const trace = {
        z: reversedMatrix,
        x: groupValues,
        y: reversedGroupValues,
        type: 'heatmap',
        colorscale: colorscaleValue,
        showscale: false
    };

    // Define layout options
    const layout = {
        title: {
            text: `Fold-differences of <br><b>${groupName}</b>`,
            font: { size: 12 },
            x: 0.5,
            xanchor: 'center',
        },
        width: 250,
        height: 250,
        xaxis: {
            ticks: '',
            ticksuffix: ' ',
            autosize: false,
            font: { size: 7 },
        },
        yaxis: {
            ticks: '',
            ticksuffix: ' ',
            autosize: false,
            font: { size: 7 },
        },
        annotations: annotations,
        margin: { l: 50, r: 50, t: 50, b: 50 },
    };

    // Create a new container for this heatmap
    const heatmapDiv = document.createElement('div');
    heatmapDiv.classList.add('heatmap-item');
    document.getElementById('heatmap-container').appendChild(heatmapDiv);
    heatmapDivs.push(heatmapDiv);

    // Create the heatmap
    Plotly.newPlot(heatmapDiv, [trace], layout);
}

let heatmapDivs = [];

export function clearHeatmaps() {
    heatmapDivs.forEach(div => {
        Plotly.purge(div);
        div.remove();
    });
    heatmapDivs = [];
}

function showTables() {
    document.getElementById('matchTable').style.display = '';
    document.getElementById('phenotypeTable').style.display = '';
    document.getElementById('adductTable').style.display = '';
    document.getElementById('fragmentTable').style.display = '';
    document.getElementById('lossesTable').style.display = '';
}

export function hideTables() {
    // Feature annotation table
    document.getElementById('matchTable').style.display = 'None';
    document.getElementById('phenotypeTable').style.display = 'None';
    document.getElementById('adductTable').style.display = 'None';
    document.getElementById('fragmentTable').style.display = 'None';
    document.getElementById('lossesTable').style.display = 'None';
    // Feature info across samples table
    document.getElementById("sampleCell").innerHTML =
    "<tr><td></td><td>Click on any feature in the main chromatogram overview.</td><td></td></tr>";
    // General feature info table
    document.getElementById('featureIdCell').textContent = '';
    document.getElementById('precMzCell').textContent = '';
    document.getElementById('retTimeCell').textContent = '';
    document.getElementById('relIntCell').innerHTML =
    'Click on any feature in the main chromatogram overview.';
    document.getElementById('absIntCell').textContent = '';
    document.getElementById('NovScore').textContent = '';
    document.getElementById('BlankAs').textContent = '';
    document.getElementById('NetworkId').textContent = '';
}