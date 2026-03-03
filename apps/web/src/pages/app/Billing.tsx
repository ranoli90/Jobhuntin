import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { Button } from "../../components/ui/Button";
import { Page } from "../../components/ui/Page";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/Table";

interface Invoice {
  id: string;
  created: number;
  total: number;
  invoice_pdf: string;
}

export default function Billing() {
  const { data: invoices = [], isLoading } = useQuery<Invoice[]>({
    queryKey: ["invoices"],
    queryFn: () => api.get<Invoice[]>("/billing/invoices")
  });

  return (
    <Page title="Billing">
      <div className="flex justify-end mb-4">
        <Button disabled>Export</Button>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Date</TableHead>
            <TableHead>Amount</TableHead>
            <TableHead>Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={3} className="text-center">
                Loading...
              </TableCell>
            </TableRow>
          ) : (
            invoices?.map((invoice) => (
              <TableRow key={invoice.id}>
                <TableCell>
                  {new Date(invoice.created * 1000).toLocaleDateString()}
                </TableCell>
                <TableCell>${(invoice.total / 100).toFixed(2)}</TableCell>
                <TableCell>
                  <a href={invoice.invoice_pdf} target="_blank" rel="noreferrer">
                    View
                  </a>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </Page>
  );
}
