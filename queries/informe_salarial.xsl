<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" indent="yes" encoding="UTF-8"/>

    <xsl:template match="/">
        <html lang="es">
        <head>
            <meta charset="UTF-8"/>
            <title>Informe Salarial por Departamento</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f4f7f6;
                    color: #333;
                    margin: 0;
                    padding: 20px;
                }
                h1 {
                    text-align: center;
                    color: #2c3e50;
                }
                table {
                    width: 90%;
                    margin: 20px auto;
                    border-collapse: collapse;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    background-color: #fff;
                }
                th, td {
                    padding: 12px 15px;
                    text-align: center;
                    border-bottom: 1px solid #ddd;
                }
                th {
                    background-color: #3498db;
                    color: white;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                }
                tr:hover {
                    background-color: #f1f1f1;
                }
                .money {
                    text-align: right;
                    font-weight: bold;
                    color: #27ae60;
                }
            </style>
        </head>
        <body>
            <h1>Informe Salarial de Departamentos</h1>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Departamento</th>
                        <th>Empleados</th>
                        <th>Salario Mín.</th>
                        <th>Salario Máx.</th>
                        <th>Salario Promedio</th>
                        <th>Masa Salarial</th>
                    </tr>
                </thead>
                <tbody>
                    <xsl:for-each select="//informe_salarial_departamento">
                        <xsl:sort select="nombre"/>
                        <tr>
                            <td><xsl:value-of select="departamento_id"/></td>
                            <td><xsl:value-of select="nombre"/></td>
                            <td><xsl:value-of select="num_empleados"/></td>
                            <td class="money">$<xsl:value-of select="format-number(salario_minimo, '#,##0.00')"/></td>
                            <td class="money">$<xsl:value-of select="format-number(salario_maximo, '#,##0.00')"/></td>
                            <td class="money">$<xsl:value-of select="format-number(salario_medio, '#,##0.00')"/></td>
                            <td class="money">$<xsl:value-of select="format-number(masa_salarial, '#,##0.00')"/></td>
                        </tr>
                    </xsl:for-each>
                </tbody>
            </table>
        </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
