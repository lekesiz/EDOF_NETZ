"use client";

interface PaginationProps {
  offset: number;
  limit: number;
  total: number;
  onChange: (offset: number) => void;
}

export function Pagination({ offset, limit, total, onChange }: PaginationProps) {
  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.ceil(total / limit);
  if (totalPages <= 1) return null;

  return (
    <div className="pagination">
      <button
        className="btn btn-outline"
        disabled={offset === 0}
        onClick={() => onChange(Math.max(0, offset - limit))}
      >
        Önceki
      </button>
      <span>
        Sayfa {currentPage} / {totalPages}
      </span>
      <button
        className="btn btn-outline"
        disabled={offset + limit >= total}
        onClick={() => onChange(offset + limit)}
      >
        Sonraki
      </button>
    </div>
  );
}
