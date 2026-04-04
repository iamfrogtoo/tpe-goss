export const AIRLINES: Record<string, string> = {
    'CI': 'CAL', 'BR': 'EVA', 'JX': 'SJX', 'IT': 'TTW',
    'CX': 'CPA', 'JL': 'JAL', 'NH': 'ANA', 'KE': 'KAL',
    'OZ': 'AAR', 'SQ': 'SIA', 'TR': 'TGW', 'PR': 'PAL',
    '5J': 'CEB', 'VN': 'HVN', 'VJ': 'VJC', 'TG': 'THA',
    'FD': 'AIQ', 'TZ': 'SCO', 'SL': 'TLM', 'AK': 'AXM',
    'OD': 'MXD', 'MH': 'MAS', 'BI': 'RBA', 'MM': 'APJ',
    'GK': 'JJP', '7C': 'JJA', 'TW': 'TWB', 'BX': 'ABL',
    'ZE': 'ESR', 'LJ': 'JNA', 'UO': 'HKE', 'HB': 'HGB',
    'HX': 'CRK', 'NX': 'AMU', 'CZ': 'CSN', 'CA': 'CCA',
    'MU': 'CES', 'HU': 'CHH', 'ZH': 'CSZ', 'SC': 'CDG',
    '3U': 'CSC', 'HO': 'DKH', '9C': 'CQH', 'FM': 'CSH',
    'TK': 'THY', 'EK': 'UAE', 'KL': 'KLM', 'DL': 'DAL',
    'UA': 'UAL', 'PO': 'PAC', 'CV': 'CLX', 'FX': 'FDX',
    '5Y': 'GTI', 'LD': 'AHK', 'KZ': 'NCA', 'RH': 'HKC',
    '7L': 'AZG', 'MF': 'CXA', 'CF': 'CYZ', '5X': 'UPS',
    'D7': 'XAX', '3K': 'JSA', 'NZ': 'ANZ', 'RF': 'EOK',
    'VZ': 'TVZ', 'OM': 'MGL', 'RS': 'ASV', 'K4': 'CKS',
    '7G': 'SFJ', 'O3': 'CSS'
};

export function parseFlightCode(rawCode: string) {
    if (!rawCode) return { icao: "", iata: "" };

    const match = rawCode.match(/^([A-Z0-9]{2,3}?)(\d+)$/);
    if (!match) return { icao: rawCode, iata: "" };

    const code = match[1];
    const num = parseInt(match[2], 10).toString();

    // If the input is a 2-letter IATA code that we know
    if (AIRLINES[code]) {
        return { icao: `${AIRLINES[code]}${num}`, iata: `${code}${num}` };
    }

    // Assume it's already an ICAO or something else
    return { icao: `${code}${num}`, iata: `${code}${num}` };
}

export function FlightCodeDisplay({ rawCode }: { rawCode: string }) {
    const { icao, iata } = parseFlightCode(rawCode);
    return (
        <>
            <span className="text-[24px] font-[800] text-white leading-none tracking-wide">{icao}</span>
            {iata && <span className="text-[14px] text-gray-400 font-mono mt-1 block">({iata})</span>}
        </>
    );
}
