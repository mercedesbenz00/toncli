# NFT Item example project

This project allows you to:

1.  Build basic nft item contract
2.  Aims to *hopefully* test any nft item contract for compliance with [NFT Standard](https://github.com/ton-blockchain/TIPs/issues/62)
3.  Deploy collection-less nft item contract via `toncli deploy`

## Building

  Just run `toncli build`
  Depending on your fift/func build you may want
  to uncomment some of the *func/helpers*

## Testing
  Build project and then: `toncli run_test`

  ⚠ If you see `6` error code on all tests - you need to update your binary [more information here](https://github.com/disintar/toncli/issues/72)

## Deploying item contract

  To deploy collection-less nft you should edit
  "fift/nft-data.fif.  
  This project is aimed mostly at testing and development of your own
  nft item contrat to be then used with *nft_collection*.  

  However, deploying collection-less NFT is still possible.

-   Set *coll_raw* address to *addr_none*.
  `0 2 u,` instead of `coll_raw Addr,` would be the
  simpest way to do it.  

-   Set *nft_json* to the full url pointing to your item metadata json

  If you aim to deploy item within collection please *use nft_collection project*.  
  To deploy run:`toncli deploy`.  

## Get nft data

`toncli get get_nft_data --fift ./fift/parse-data-nft-single.fif`
