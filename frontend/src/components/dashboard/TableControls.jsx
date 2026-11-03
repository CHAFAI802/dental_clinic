import { useState } from 'react'

export function TableSearch({
  value,
  onChange,
  label,
  placeholder,
}) {
  return (
    <div className="form-shell table-search">
      <input
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        aria-label={label}
      />
    </div>
  )
}

export function TablePagination({
  page,
  pageSize,
  totalItems,
  onPageChange,
  onPageSizeChange,
  label = 'des résultats',
}) {
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize))
  const currentPage = Math.min(Math.max(page, 1), totalPages)

  return (
    <nav className="table-pagination" aria-label={`Pagination ${label}`}>
      <label className="table-page-size">
        Éléments par page
        <select
          value={pageSize}
          onChange={(event) => onPageSizeChange(Number(event.target.value))}
        >
          {[10, 20, 50].map((size) => (
            <option key={size} value={size}>{size}</option>
          ))}
        </select>
      </label>

      <button
        type="button"
        className="btn btn-outline btn-sm"
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage <= 1}
      >
        Précédent
      </button>

      <span className="table-pagination-status" aria-live="polite">
        Page {currentPage} / {totalPages} · {totalItems} résultat{totalItems > 1 ? 's' : ''}
      </span>

      <button
        type="button"
        className="btn btn-outline btn-sm"
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage >= totalPages}
      >
        Suivant
      </button>
    </nav>
  )
}

export function normalizeTableSearch(value) {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase()
}

export function filterTableRows(rows, query, getSearchValues) {
  const normalizedQuery = normalizeTableSearch(query.trim())
  if (!normalizedQuery) return rows

  return rows.filter((row) =>
    getSearchValues(row).some((value) =>
      normalizeTableSearch(value).includes(normalizedQuery),
    ),
  )
}

export function paginateTableRows(rows, page, pageSize) {
  const totalPages = Math.max(1, Math.ceil(rows.length / pageSize))
  const currentPage = Math.min(Math.max(page, 1), totalPages)
  const start = (currentPage - 1) * pageSize

  return {
    items: rows.slice(start, start + pageSize),
    currentPage,
    totalPages,
  }
}

export function SearchableTable({
  rows,
  getSearchValues,
  searchLabel,
  placeholder,
  emptyMessage,
  paginationLabel,
  renderTable,
}) {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const filteredRows = filterTableRows(rows, search, getSearchValues)
  const { items, currentPage } = paginateTableRows(filteredRows, page, pageSize)

  return (
    <>
      <TableSearch
        value={search}
        onChange={(value) => {
          setSearch(value)
          setPage(1)
        }}
        label={searchLabel}
        placeholder={placeholder}
      />
      {filteredRows.length === 0 ? (
        <p>{emptyMessage}</p>
      ) : (
        <>
          {renderTable(items)}
          <TablePagination
            page={currentPage}
            pageSize={pageSize}
            totalItems={filteredRows.length}
            onPageChange={setPage}
            onPageSizeChange={(size) => {
              setPageSize(size)
              setPage(1)
            }}
            label={paginationLabel}
          />
        </>
      )}
    </>
  )
}
