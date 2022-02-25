for (let row of mytab.rows) {
	cell = row.cells[6];
	if (cell.innerText == "") {
		row.style.display = 'none';
	}
}
