import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { Button } from "../../components/ui/Button";
import { Page } from "../../components/ui/Page";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/Table";
import { FileText, Download, Loader2 } from "lucide-react";

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
    <Page title="Billing History">
      <div className="space-y-6">
        {/* Billing Summary Card */}
        <div className="bg-slate-50 dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800">
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-2">Billing Overview</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            View and download your invoices. All transactions are securely processed through Stripe.
          </p>
        </div>

        {/* Invoices Table */}
        <div className="overflow-x-auto -mx-4 px-4 sm:mx-0 sm:px-0">
          <div className="inline-block min-w-full align-middle">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="min-w-[120px]">Date</TableHead>
                  <TableHead className="min-w-[100px]">Amount</TableHead>
                  <TableHead className="min-w-[100px] text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={3} className="text-center py-8">
                      <div className="flex items-center justify-center gap-2 text-slate-500">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Loading invoices...
                      </div>
                    </TableCell>
                  </TableRow>
                ) : invoices?.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} className="text-center py-12">
                      <div className="flex flex-col items-center gap-3">
                        <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center">
                          <FileText className="w-6 h-6 text-slate-400" />
                        </div>
                        <div>
                          <p className="text-slate-900 font-medium">No invoices yet</p>
                          <p className="text-sm text-slate-500">Your billing history will appear here</p>
                        </div>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  invoices?.map((invoice) => (
                    <TableRow key={invoice.id}>
                      <TableCell className="font-medium">
                        {new Date(invoice.created * 1000).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric'
                        })}
                      </TableCell>
                      <TableCell className="font-bold text-slate-900">
                        ${(invoice.total / 100).toFixed(2)}
                      </TableCell>
                      <TableCell className="text-right">
                        <a 
                          href={invoice.invoice_pdf} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 text-indigo-600 hover:text-indigo-700 font-medium text-sm hover:underline focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 rounded"
                          aria-label={`Download invoice from ${new Date(invoice.created * 1000).toLocaleDateString()}`}
                        >
                          <Download className="w-4 h-4" />
                          Download
                        </a>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      </div>
    </Page>
  );
}
