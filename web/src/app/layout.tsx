import "./globals.css";
import { AuthProvider } from "@/lib/auth";

export const metadata = {
  title: "EDOF-NETZ",
  description: "CPF/EDOF Yönetim ERP",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
