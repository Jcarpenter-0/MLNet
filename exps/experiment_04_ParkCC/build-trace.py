import networks.mahimahi

lines = networks.mahimahi.MakeMahiMahiLinkFile(48)

fp = open('./const48.mahi', 'w')
fp.writelines(lines)
fp.flush()
fp.close()