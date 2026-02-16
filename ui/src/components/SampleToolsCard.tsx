import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Wrench, FileText, Binary, Search } from 'lucide-react'
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
  Input,
  Spinner,
} from '@/components/ui'
import { gqlQuery } from '@/lib/graphql'

interface SampleToolsCardProps {
  md5: string
  bare?: boolean
}

type ToolTab = 'strings' | 'hex' | 'xor'

const STRINGS_QUERY = `
  query SampleStrings($md5: String!) {
    sampleStrings(md5: $md5)
  }
`

const HEX_QUERY = `
  query SampleHex($md5: String!, $length: Int) {
    sampleHex(md5: $md5, length: $length)
  }
`

const XOR_QUERY = `
  query SampleXorSearch($md5: String!, $searchString: String, $skipNulls: Int) {
    sampleXorSearch(md5: $md5, searchString: $searchString, skipNulls: $skipNulls)
  }
`

export function SampleToolsCard({ md5, bare }: SampleToolsCardProps) {
  const [activeTab, setActiveTab] = useState<ToolTab | null>(null)
  const [xorInput, setXorInput] = useState('')

  const strings = useQuery({
    queryKey: ['sampleStrings', md5],
    queryFn: () => gqlQuery<{ sampleStrings: string | null }>(STRINGS_QUERY, { md5 }),
    enabled: false,
  })

  const hex = useQuery({
    queryKey: ['sampleHex', md5],
    queryFn: () => gqlQuery<{ sampleHex: string | null }>(HEX_QUERY, { md5, length: 4096 }),
    enabled: false,
  })

  const xor = useQuery({
    queryKey: ['sampleXorSearch', md5, xorInput],
    queryFn: () =>
      gqlQuery<{ sampleXorSearch: number[] }>(XOR_QUERY, {
        md5,
        searchString: xorInput || null,
        skipNulls: 0,
      }),
    enabled: false,
  })

  const handleTabClick = (tab: ToolTab) => {
    setActiveTab(tab)
    if (tab === 'strings' && !strings.data) strings.refetch()
    if (tab === 'hex' && !hex.data) hex.refetch()
  }

  const content = (
    <>
      <div className="flex gap-2 mb-4">
        <Button
          variant={activeTab === 'strings' ? 'primary' : 'ghost'}
          size="sm"
          onClick={() => handleTabClick('strings')}
        >
          <FileText className="h-3.5 w-3.5 mr-1" />
          Strings
        </Button>
        <Button
          variant={activeTab === 'hex' ? 'primary' : 'ghost'}
          size="sm"
          onClick={() => handleTabClick('hex')}
        >
          <Binary className="h-3.5 w-3.5 mr-1" />
          Hex
        </Button>
        <Button
          variant={activeTab === 'xor' ? 'primary' : 'ghost'}
          size="sm"
          onClick={() => {
            setActiveTab('xor')
          }}
        >
          <Search className="h-3.5 w-3.5 mr-1" />
          XOR
        </Button>
      </div>

      {activeTab === 'strings' && (
        <div>
          {strings.isLoading || strings.isFetching ? (
            <div className="flex justify-center py-4">
              <Spinner size="sm" />
            </div>
          ) : strings.data?.sampleStrings ? (
            <pre className="text-xs font-mono bg-light-surface dark:bg-dark-surface p-3 rounded overflow-auto max-h-96 whitespace-pre-wrap">
              {strings.data.sampleStrings}
            </pre>
          ) : (
            <p className="text-sm text-light-text-muted dark:text-dark-text-muted">
              No strings found
            </p>
          )}
        </div>
      )}

      {activeTab === 'hex' && (
        <div>
          {hex.isLoading || hex.isFetching ? (
            <div className="flex justify-center py-4">
              <Spinner size="sm" />
            </div>
          ) : hex.data?.sampleHex ? (
            <pre className="text-xs font-mono bg-light-surface dark:bg-dark-surface p-3 rounded overflow-auto max-h-96">
              {hex.data.sampleHex}
            </pre>
          ) : (
            <p className="text-sm text-light-text-muted dark:text-dark-text-muted">
              No hex data available
            </p>
          )}
        </div>
      )}

      {activeTab === 'xor' && (
        <div className="space-y-3">
          <div className="flex gap-2">
            <Input
              placeholder="Search string (e.g. MZ, This program)"
              value={xorInput}
              onChange={(e) => setXorInput(e.target.value)}
              className="text-sm"
            />
            <Button size="sm" onClick={() => xor.refetch()} disabled={xor.isFetching}>
              Search
            </Button>
          </div>
          {(xor.isLoading || xor.isFetching) && (
            <div className="flex justify-center py-4">
              <Spinner size="sm" />
            </div>
          )}
          {xor.data?.sampleXorSearch && !xor.isFetching && (
            <div>
              {xor.data.sampleXorSearch.length === 0 ? (
                <p className="text-sm text-light-text-muted dark:text-dark-text-muted">
                  No XOR keys found
                </p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {xor.data.sampleXorSearch.map((key) => (
                    <Badge key={key} variant="info" className="font-mono">
                      0x{key.toString(16).toUpperCase().padStart(2, '0')}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </>
  )

  if (bare) {
    return content
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wrench className="h-5 w-5" />
          Tools
        </CardTitle>
      </CardHeader>
      <CardContent>{content}</CardContent>
    </Card>
  )
}
